# -*- coding: utf-8 -*-
import base64
import csv
import io
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import xlsxwriter
except ImportError:
    _logger.warning("xlsxwriter no está disponible. La exportación XLSX no funcionará.")
    xlsxwriter = None

# Columnas exportadas: (etiqueta, lambda de extracción)
_COLUMNS = [
    (_('Nº Aplicación'),    lambda a: a.application_number or ''),
    (_('Nombre'),           lambda a: a.name or ''),
    (_('Email'),            lambda a: a.email or ''),
    (_('Teléfono'),         lambda a: a.phone or ''),
    (_('Móvil'),            lambda a: a.mobile or ''),
    (_('Fecha Aplicación'), lambda a: a.application_date.strftime('%d/%m/%Y %H:%M') if a.application_date else ''),
    (_('Fecha Admisión'),   lambda a: a.admission_date.strftime('%d/%m/%Y') if a.admission_date else ''),
    (_('Curso'),            lambda a: a.course_id.name if a.course_id else ''),
    (_('Lote'),             lambda a: a.batch_id.name if a.batch_id else ''),
    (_('Estado'),           lambda a: dict(a._fields['state'].selection).get(a.state, a.state or '')),
]


class IrgAdmissionExportWizard(models.TransientModel):
    _name = 'irg.admission.export.wizard'
    _description = 'Exportar admisiones a CSV o XLSX'

    register_id = fields.Many2one(
        'op.admission.register',
        string=_('Registro de Admisión'),
        readonly=True,
    )
    export_format = fields.Selection(
        [('csv', 'CSV'), ('xlsx', 'Excel (XLSX)')],
        string=_('Formato'),
        default='xlsx',
        required=True,
    )
    file_data = fields.Binary(string=_('Archivo'), readonly=True)
    filename = fields.Char(string=_('Nombre del archivo'), readonly=True)
    state = fields.Selection(
        [('choose', 'Elegir'), ('done', 'Hecho')],
        default='choose',
    )

    # ------------------------------------------------------------------
    # Default
    # ------------------------------------------------------------------

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            res['register_id'] = active_id
        return res

    # ------------------------------------------------------------------
    # Action
    # ------------------------------------------------------------------

    def action_export(self):
        self.ensure_one()
        if not self.register_id:
            raise UserError(_('No se ha seleccionado ningún registro de admisión.'))
        admissions = self.register_id.admission_ids
        if not admissions:
            raise UserError(_('Este registro no tiene admisiones que exportar.'))

        if self.export_format == 'csv':
            file_bytes, ext = self._build_csv(admissions)
        else:
            if xlsxwriter is None:
                raise UserError(_('La librería xlsxwriter no está instalada. Usa el formato CSV.'))
            file_bytes, ext = self._build_xlsx(admissions)

        date_str = fields.Date.today().strftime('%Y%m%d')
        safe_name = (self.register_id.name or 'export').replace('/', '-').replace(' ', '_')
        filename = f'admisiones_{safe_name}_{date_str}.{ext}'

        self.write({
            'file_data': base64.b64encode(file_bytes).decode(),
            'filename': filename,
            'state': 'done',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    def _get_rows(self, admissions):
        """Devuelve (cabeceras, [[fila], ...])."""
        headers = [col[0] for col in _COLUMNS]
        rows = [[col[1](adm) for col in _COLUMNS] for adm in admissions]
        return headers, rows

    def _build_csv(self, admissions):
        headers, rows = self._get_rows(admissions)
        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        writer.writerows(rows)
        # UTF-8 BOM para que Excel no rompa los acentos al abrir directamente
        file_bytes = output.getvalue().encode('utf-8-sig')
        return file_bytes, 'csv'

    def _build_xlsx(self, admissions):
        headers, rows = self._get_rows(admissions)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(_('Admisiones'))

        # Formatos
        bold = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
        cell = workbook.add_format({'border': 1})

        # Cabecera
        for col_idx, header in enumerate(headers):
            sheet.write(0, col_idx, header, bold)

        # Datos
        for row_idx, row in enumerate(rows, start=1):
            for col_idx, value in enumerate(row):
                sheet.write(row_idx, col_idx, value, cell)

        # Ajustar ancho de columnas (estimado)
        col_widths = [max(len(str(headers[i])), *(len(str(r[i])) for r in rows)) + 2
                      for i in range(len(headers))]
        for col_idx, width in enumerate(col_widths):
            sheet.set_column(col_idx, col_idx, min(width, 40))

        workbook.close()
        file_bytes = output.getvalue()
        return file_bytes, 'xlsx'
