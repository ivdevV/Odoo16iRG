# -*- coding: utf-8 -*-
import csv
import io
import logging
import os
import re
import shutil
from collections import defaultdict
from datetime import datetime, timedelta

import pytz

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────────────────────
SPAIN_TZ = 'Europe/Madrid'
SESSION_START_HOUR = 16   # 16:00 hora España
SESSION_END_HOUR = 21     # 21:00 hora España
SUBJECT_UNLOCK_HOURS = 72  # Horas antes de la primera sesión que se habilita el contenido

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
    subject_dates_updated = fields.Integer(
        string=_('Fechas habilitación actualizadas'), readonly=True
    )
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
                dates_updated, dates_errors = self._update_subject_to_batch_dates(parsed)
                errors.extend(dates_errors)

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
                    'subject_dates_updated': dates_updated,
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

        Formato esperado (5 columnas, separador ';' o ','):
            Col 0: Máster/Programa  (ej: "Calendario NC 365")
            Col 1: PestañaOrig      (ej: "feb-26") — se ignora
            Col 2: Fecha            (ej: "06/02/2026 0:00" — DD/MM/YYYY)
            Col 3: Nombre Asignatura
            Col 4: Docente

        La fila 0 es la cabecera global y se omite.
        Filas con menos de 5 columnas, sin fecha válida o que empiecen
        por '*' se ignoran silenciosamente.

        Returns:
            list[dict]: claves program_label, date, subject_name, faculty_name
        """
        delimiter = ';' if content.count(';') >= content.count(',') else ','
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        rows = list(reader)

        sessions = []

        for i, row in enumerate(rows):
            if i == 0:
                # Cabecera global exportada desde pandas/Excel — omitir
                continue

            if len(row) < 5:
                continue

            col0 = row[0].strip()  # Máster/Programa
            # col1 = row[1]        # PestañaOrig — ignorar
            col2 = row[2].strip()  # Fecha DD/MM/YYYY [HH:MM]
            col3 = row[3].strip()  # Nombre Asignatura
            col4 = row[4].strip()  # Docente

            if not col0 or col0.startswith('*'):
                continue
            if not col2 or not col3:
                continue

            # Parsear fecha DD/MM/YYYY — tomamos solo los primeros 10 chars
            try:
                session_date = datetime.strptime(col2[:10], '%d/%m/%Y').date()
            except ValueError:
                # Puede llegar en formato YYYY-MM-DD desde algunas exportaciones
                try:
                    session_date = datetime.strptime(col2[:10], '%Y-%m-%d').date()
                except ValueError:
                    continue

            sessions.append({
                'program_label': col0,
                'date': session_date,
                'subject_name': col3,
                'faculty_name': col4,
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

    # ─── Subject-to-batch date updater ───────────────────────────────────────

    @api.model
    def _update_subject_to_batch_dates(self, parsed_rows):
        """Calcula date_from/date_to en op.subject.to.batch desde las filas parseadas.

        Lógica:
          - date_from = fecha mínima de sesión de esa asignatura en el lote
                        menos SUBJECT_UNLOCK_HOURS horas
          - date_to   = batch.end_date  (permanece accesible hasta cierre del lote)

        Solo actualiza registros existentes; no crea nuevos (los crea el flujo
        de admisiones al matricular al alumno).

        Returns:
            list[str]: mensajes de advertencia/error ocurridos
        """
        ProgramMap = self.env['irg.timetable.program.map']
        SubjectToBatch = self.env['op.subject.to.batch']
        Subject = self.env['op.subject']
        Batch = self.env['op.batch']
        errors = []
        count = 0

        # Construir mapa: (program_label, subject_name) → min_date
        min_dates = {}  # (prog_label, subject_name_lower) → date
        for row in parsed_rows:
            key = (row['program_label'], row['subject_name'].strip().lower())
            if key not in min_dates or row['date'] < min_dates[key]:
                min_dates[key] = row['date']

        # Agrupar por programa
        prog_subjects = defaultdict(set)
        for (prog_label, subj_lower) in min_dates:
            prog_subjects[prog_label].add(subj_lower)

        for prog_label, subj_names_lower in sorted(prog_subjects.items()):

            mapping = ProgramMap.search(
                [('csv_label', '=', prog_label), ('active', '=', True)], limit=1
            )
            if not mapping:
                continue  # ya reportado en _process_sessions

            course = mapping.course_id
            if mapping.batch_id:
                batches = mapping.batch_id
            else:
                batches = Batch.search([
                    ('course_id', '=', course.id),
                    ('active', '=', True),
                ])

            if not batches:
                continue

            for subj_lower in subj_names_lower:
                min_date = min_dates[(prog_label, subj_lower)]
                # date_from = primera sesión - 72h (como date)
                date_from = (datetime.combine(min_date, datetime.min.time())
                             - timedelta(hours=SUBJECT_UNLOCK_HOURS)).date()

                # Resolver asignatura
                subject = course.subject_ids.filtered(
                    lambda s, n=subj_lower: s.name.strip().lower() == n
                )
                if not subject:
                    subject = Subject.search(
                        [('name', '=ilike', subj_lower)], limit=1
                    )
                if not subject:
                    continue  # ya reportado en _process_sessions
                subject = subject[:1]

                for batch in batches:
                    date_to = batch.end_date

                    stb = SubjectToBatch.search([
                        ('batch_id', '=', batch.id),
                        ('subject_id', '=', subject.id),
                    ], limit=1)

                    if stb:
                        if stb.date_from != date_from or stb.date_to != date_to:
                            stb.sudo().write({
                                'date_from': date_from,
                                'date_to': date_to,
                            })
                            count += 1
                            _logger.info(
                                'irg_timetable_csv_import: op.subject.to.batch[%d] '
                                'actualizado date_from=%s date_to=%s',
                                stb.id, date_from, date_to,
                            )
                    else:
                        errors.append(
                            'No existe op.subject.to.batch para asignatura "%s" '
                            'en lote "%s" — crea la matrícula del alumno primero '
                            'o añade la asignatura al lote manualmente.' % (
                                subject.name, batch.name
                            )
                        )

        return count, errors
