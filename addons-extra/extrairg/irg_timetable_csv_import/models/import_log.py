# -*- coding: utf-8 -*-
import csv
import io
import logging
import os
import re
import shutil
from collections import defaultdict
from datetime import datetime

import pytz

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────────────────────
SPAIN_TZ = 'Europe/Madrid'
SESSION_START_HOUR = 16   # 16:00 hora España
SESSION_END_HOUR = 21     # 21:00 hora España

# Regex to strip academic title prefixes from faculty names
_FACULTY_PREFIX_RE = re.compile(
    r'^(?:Prof\.?\s+|Dr\.?\s+|Dra\.?\s+|Lic\.?\s+|Ing\.?\s+)', re.IGNORECASE
)


class IrgTimetableImportLog(models.Model):
    """Log de cada importación CSV y punto de entrada del cron."""

    _name = 'irg.timetable.import.log'
    _description = 'Log de importación de calendarios académicos CSV'
    _order = 'import_date desc'

    name = fields.Char(string=_('Archivo'), required=True, readonly=True)
    import_date = fields.Datetime(
        string=_('Fecha de importación'),
        default=fields.Datetime.now,
        readonly=True,
    )
    state = fields.Selection(
        [('ok', 'OK'), ('warning', 'Advertencias'), ('error', 'Error')],
        string=_('Estado'),
        readonly=True,
    )
    sessions_created = fields.Integer(string=_('Sesiones creadas'), readonly=True)
    sessions_updated = fields.Integer(string=_('Sesiones actualizadas'), readonly=True)
    sessions_skipped = fields.Integer(string=_('Omitidas / errores'), readonly=True)
    error_details = fields.Text(
        string=_('Detalle de errores / advertencias'), readonly=True
    )

    # ─── Cron entry point ────────────────────────────────────────────────────

    @api.model
    def cron_process_csv_directory(self):
        """Escanea watch_dir e importa todos los CSV encontrados.

        Respeta la guarda de upgrades (Biblia §6.3): si hay módulos
        pendientes no hace nada.
        """
        # Guarda de upgrades (Biblia §6.3)
        pending = self.env['ir.module.module'].sudo().search_count(
            [('state', 'in', ['to install', 'to upgrade', 'to remove'])]
        )
        if pending:
            _logger.info('irg_timetable_csv_import: omitiendo cron — módulos pendientes')
            return

        ICP = self.env['ir.config_parameter'].sudo()
        watch_dir = ICP.get_param('irg_timetable_csv_import.watch_dir', '')

        if not watch_dir:
            _logger.warning(
                'irg_timetable_csv_import: watch_dir no configurado. '
                'Ajusta Ajustes Técnicos > Parámetros del sistema > '
                'irg_timetable_csv_import.watch_dir'
            )
            return

        if not os.path.isdir(watch_dir):
            _logger.warning(
                'irg_timetable_csv_import: watch_dir no existe o no es un directorio: %s',
                watch_dir,
            )
            return

        processed_dir = os.path.join(watch_dir, 'processed')
        failed_dir = os.path.join(watch_dir, 'failed')
        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(failed_dir, exist_ok=True)

        csv_files = sorted(
            f for f in os.listdir(watch_dir)
            if f.lower().endswith('.csv')
            and os.path.isfile(os.path.join(watch_dir, f))
        )
        if not csv_files:
            return

        for fname in csv_files:
            fpath = os.path.join(watch_dir, fname)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            try:
                with open(fpath, 'r', encoding='utf-8-sig') as fh:
                    content = fh.read()

                parsed = self._parse_csv(content)
                created, updated, skipped, errors = self._process_sessions(parsed)

                if errors and (created + updated) == 0:
                    state = 'error'
                elif errors:
                    state = 'warning'
                else:
                    state = 'ok'

                self.create({
                    'name': fname,
                    'state': state,
                    'sessions_created': created,
                    'sessions_updated': updated,
                    'sessions_skipped': skipped,
                    'error_details': '\n'.join(errors) if errors else False,
                })

                dest = os.path.join(processed_dir, '%s_%s' % (ts, fname))
                shutil.move(fpath, dest)
                _logger.info(
                    'irg_timetable_csv_import: %s procesado → '
                    'creadas=%d actualizadas=%d omitidas=%d',
                    fname, created, updated, skipped,
                )

            except Exception:
                _logger.exception(
                    'irg_timetable_csv_import: error inesperado procesando %s', fname
                )
                dest = os.path.join(failed_dir, '%s_%s' % (ts, fname))
                shutil.move(fpath, dest)
                self.create({
                    'name': fname,
                    'state': 'error',
                    'sessions_created': 0,
                    'sessions_updated': 0,
                    'sessions_skipped': 0,
                    'error_details': _(
                        'Error inesperado al procesar el archivo. '
                        'Revisa los logs del servidor para detalles.'
                    ),
                })

    # ─── CSV Parser ──────────────────────────────────────────────────────────

    @api.model
    def _parse_csv(self, content):
        """Parsea el formato CSV de calendarios académicos IRG.

        Formato esperado (separador ';'):
            Row 0: cabecera global (Máster/Programa; Unnamed:0 ; …)
            Row N: «Calendario XX 365;Fecha;Nombre Asignatura;Docente»  ← inicio sección
            Row N+k: «Calendario XX 365;2026-02-06 00:00:00;Nombre asig;Docente»
            Row N+m: «Calendario XX 365;* Calendario sujeto a…»  ← nota, ignorar

        Returns:
            list[dict]: claves program_label, date, subject_name, faculty_name
        """
        delimiter = ';' if content.count(';') >= content.count(',') else ','
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        rows = list(reader)

        sessions = []
        current_program = None

        for i, row in enumerate(rows):
            if i == 0:
                # Cabecera global del CSV exportado desde pandas/Excel — omitir
                continue

            if len(row) < 2:
                continue

            col0 = row[0].strip()
            col1 = row[1].strip() if len(row) > 1 else ''
            col2 = row[2].strip() if len(row) > 2 else ''
            col3 = row[3].strip() if len(row) > 3 else ''

            # Fila de cabecera de sección: «Calendario NC 365;Fecha;…»
            if col1 == 'Fecha':
                current_program = col0
                continue

            # Ignorar si aún no hemos encontrado ninguna sección
            if not current_program:
                continue

            # Notas o filas vacías
            if not col1 or col1.startswith('*') or col1.lower().startswith('clases'):
                continue

            # Intentar parsear fecha (YYYY-MM-DD o YYYY-MM-DD HH:MM:SS)
            try:
                session_date = datetime.strptime(col1[:10], '%Y-%m-%d').date()
            except ValueError:
                continue

            if not col2:
                continue

            sessions.append({
                'program_label': col0 or current_program,
                'date': session_date,
                'subject_name': col2,
                'faculty_name': col3,
            })

        return sessions

    # ─── Session creator / updater ───────────────────────────────────────────

    @api.model
    def _process_sessions(self, parsed_rows):
        """Crea o actualiza registros op.session a partir de las filas parseadas.

        Deduplicación: (batch_id, subject_id, start_datetime).
        Si faculty o asignatura no existen → log error, omite la fila.

        Returns:
            tuple: (created:int, updated:int, skipped:int, errors:list[str])
        """
        ProgramMap = self.env['irg.timetable.program.map']
        Session = self.env['op.session']
        Faculty = self.env['op.faculty']
        Subject = self.env['op.subject']
        Batch = self.env['op.batch']
        spain_tz = pytz.timezone(SPAIN_TZ)

        created = updated = skipped = 0
        errors = []

        # Agrupar por programa para minimizar búsquedas de batch/mapeo
        by_program = defaultdict(list)
        for row in parsed_rows:
            by_program[row['program_label']].append(row)

        for prog_label, rows in sorted(by_program.items()):

            # ── 1. Resolver mapeo ─────────────────────────────────────────
            mapping = ProgramMap.search(
                [('csv_label', '=', prog_label), ('active', '=', True)], limit=1
            )
            if not mapping:
                errors.append(
                    'Sin mapeo configurado para "%s" — %d fila(s) omitida(s). '
                    'Añade el mapeo en Horarios > Configuración > Mapeos CSV.' % (
                        prog_label, len(rows)
                    )
                )
                skipped += len(rows)
                continue

            course = mapping.course_id

            # ── 2. Resolver lotes ─────────────────────────────────────────
            if mapping.batch_id:
                batches = mapping.batch_id
            else:
                batches = Batch.search([
                    ('course_id', '=', course.id),
                    ('active', '=', True),
                ])

            if not batches:
                errors.append(
                    'Sin lotes activos para "%s" (%s) — %d fila(s) omitida(s).' % (
                        course.name, prog_label, len(rows)
                    )
                )
                skipped += len(rows)
                continue

            # ── 3. Procesar cada fila ─────────────────────────────────────
            for row in rows:
                subject_name = row['subject_name'].strip()
                faculty_raw = row['faculty_name'].strip()

                # Resolver asignatura: primero en el curso, luego global
                subject = course.subject_ids.filtered(
                    lambda s, n=subject_name: s.name.strip().lower() == n.lower()
                )
                if not subject:
                    subject = Subject.search(
                        [('name', '=ilike', subject_name)], limit=1
                    )
                if not subject:
                    # Intento parcial (warn)
                    subject = Subject.search(
                        [('name', 'ilike', subject_name)], limit=1
                    )
                    if subject:
                        errors.append(
                            'Asignatura "%s" encontrada por coincidencia parcial '
                            '→ usando "%s" [%s %s]' % (
                                subject_name, subject.name, prog_label, row['date']
                            )
                        )
                if not subject:
                    errors.append(
                        'Asignatura no encontrada: "%s" [%s %s]' % (
                            subject_name, prog_label, row['date']
                        )
                    )
                    skipped += 1
                    continue
                subject = subject[:1]

                # Resolver docente
                clean_name = _FACULTY_PREFIX_RE.sub('', faculty_raw).strip()
                faculty = Faculty.search([
                    '|',
                    ('partner_id.name', '=ilike', faculty_raw),
                    ('partner_id.name', '=ilike', clean_name),
                ], limit=1)
                if not faculty and clean_name:
                    # Búsqueda por apellido (última palabra)
                    last_word = clean_name.split()[-1]
                    if len(last_word) > 3:
                        faculty = Faculty.search(
                            [('partner_id.name', 'ilike', last_word)], limit=1
                        )
                        if faculty:
                            errors.append(
                                'Docente "%s" vinculado por apellido → '
                                '"%s" [%s %s]' % (
                                    faculty_raw, faculty.partner_id.name,
                                    prog_label, row['date']
                                )
                            )
                if not faculty:
                    errors.append(
                        'Docente no encontrado: "%s" [%s %s]' % (
                            faculty_raw, prog_label, row['date']
                        )
                    )
                    skipped += 1
                    continue

                # Calcular datetimes: Spain TZ → UTC (sin tzinfo para Odoo)
                start_local = spain_tz.localize(
                    datetime(
                        row['date'].year, row['date'].month, row['date'].day,
                        SESSION_START_HOUR, 0, 0,
                    )
                )
                end_local = spain_tz.localize(
                    datetime(
                        row['date'].year, row['date'].month, row['date'].day,
                        SESSION_END_HOUR, 0, 0,
                    )
                )
                start_utc = start_local.astimezone(pytz.utc).replace(tzinfo=None)
                end_utc = end_local.astimezone(pytz.utc).replace(tzinfo=None)

                for batch in batches:
                    vals = {
                        'course_id': course.id,
                        'batch_id': batch.id,
                        'subject_id': subject.id,
                        'faculty_id': faculty.id,
                        'start_datetime': start_utc,
                        'end_datetime': end_utc,
                        'state': 'confirm',
                    }

                    existing = Session.search([
                        ('batch_id', '=', batch.id),
                        ('subject_id', '=', subject.id),
                        ('start_datetime', '=', start_utc),
                    ], limit=1)

                    if existing:
                        changed = (
                            existing.faculty_id.id != faculty.id
                            or existing.end_datetime != end_utc
                        )
                        if changed:
                            existing.write(vals)
                            updated += 1
                        # Sin cambios → no-op (idempotente)
                    else:
                        Session.create(vals)
                        created += 1

        return created, updated, skipped, errors
