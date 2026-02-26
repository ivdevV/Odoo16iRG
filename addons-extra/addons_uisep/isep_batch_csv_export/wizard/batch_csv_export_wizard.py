# -*- coding: utf-8 -*-

import base64
import csv
import io
import xlsxwriter
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BatchCsvExportWizard(models.TransientModel):
    _name = 'batch.csv.export.wizard'
    _description = 'Wizard para exportar estudiantes del lote a CSV'

    batch_id = fields.Many2one('op.batch', string='Lote', readonly=True)
    csv_file = fields.Binary(string='Archivo CSV', readonly=True)
    csv_filename = fields.Char(string='Nombre del archivo')
    excel_file = fields.Binary(string='Archivo Excel', readonly=True)
    excel_filename = fields.Char(string='Nombre del archivo Excel')
    state = fields.Selection([
        ('choose', 'Elegir'),
        ('done', 'Hecho')
    ], default='choose', string='Estado')

    @api.model
    def default_get(self, fields_list):
        res = super(BatchCsvExportWizard, self).default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id:
            res['batch_id'] = active_id
        return res

    def _get_csv_headers(self):
        """Define los encabezados del CSV"""
        return [
            'Número de Aplicación',
            'Lote',
            'Nombre',
            'Correo electrónico',
            'Fecha de Admisión',
            'Fecha de Aplicación',
            'Curso',
            'Estado de Pago',
            'TFM',
            'Prácticas',
            'Estado',
        ]

    def _get_admission_row(self, admission):
        """Obtiene una fila de datos para una admisión"""
        # Estado de pago
        payment_state = ''
        if hasattr(admission, 'pending_payments'):
            payment_state = 'Pendiente' if admission.pending_payments else 'Al corriente'
        elif hasattr(admission, 'payment_state'):
            payment_state = dict(admission._fields['payment_state'].selection).get(admission.payment_state, '') if admission.payment_state else ''
        
        # TFM
        tfm = ''
        if hasattr(admission, 'tfm_state'):
            tfm = dict(admission._fields['tfm_state'].selection).get(admission.tfm_state, '') if admission.tfm_state else ''
        elif hasattr(admission, 'tfm'):
            tfm = admission.tfm or ''
            
        # Prácticas
        practicas = ''
        if hasattr(admission, 'practices_state'):
            practicas = dict(admission._fields['practices_state'].selection).get(admission.practices_state, '') if admission.practices_state else ''
        elif hasattr(admission, 'practices'):
            practicas = admission.practices or ''

        # Estado
        state = ''
        if admission.state:
            state = dict(admission._fields['state'].selection).get(admission.state, '')

        email = ''
        if admission.student_id and admission.student_id.partner_id and admission.student_id.partner_id.email:
            email = admission.student_id.partner_id.email
        elif admission.email:
            email = admission.email

        return [
            admission.application_number or '',
            admission.batch_id.name if admission.batch_id else '',
            admission.name or '',
            email,
            admission.admission_date.strftime('%d/%m/%Y') if admission.admission_date else '',
            admission.application_date.strftime('%d/%m/%Y %H:%M:%S') if admission.application_date else '',
            admission.course_id.name if admission.course_id else '',
            payment_state,
            tfm,
            practicas,
            state,
        ]

    def _get_admissions(self):
        self.ensure_one()
        return self.env['op.admission'].search([
            ('batch_id', '=', self.batch_id.id),
            ('state', '=', 'done')
        ], order='application_date desc')

    def _build_export_filename(self, extension):
        base_name = self.batch_id.code or self.batch_id.name or 'lote'
        date_str = fields.Date.today().strftime('%Y%m%d')
        return f"estudiantes_{base_name}_{date_str}.{extension}"

    def action_export_csv(self):
        """Genera el archivo CSV con los estudiantes del lote"""
        self.ensure_one()
        
        if not self.batch_id:
            raise UserError(_('No se ha seleccionado ningún lote.'))
        
        # Buscar admisiones del lote
        admissions = self._get_admissions()
        
        if not admissions:
            raise UserError(_('No hay estudiantes en este lote.'))
        
        # Crear el CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Escribir encabezados
        writer.writerow(self._get_csv_headers())
        
        # Escribir datos
        for admission in admissions:
            writer.writerow(self._get_admission_row(admission))
        
        # Convertir a base64 con BOM para Excel
        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')
        csv_base64 = base64.b64encode(csv_bytes).decode()
        
        # Actualizar el wizard
        filename = self._build_export_filename('csv')
        self.write({
            'csv_file': csv_base64,
            'csv_filename': filename,
            'state': 'done',
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'batch.csv.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }

    def action_export_excel(self):
        """Genera el archivo Excel con los estudiantes del lote"""
        self.ensure_one()

        if not self.batch_id:
            raise UserError(_('No se ha seleccionado ningún lote.'))

        admissions = self._get_admissions()

        if not admissions:
            raise UserError(_('No hay estudiantes en este lote.'))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Estudiantes')

        header_format = workbook.add_format({'bold': True, 'bg_color': '#D9E1F2', 'border': 1})
        cell_format = workbook.add_format({'border': 1})

        headers = self._get_csv_headers()
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        for row_index, admission in enumerate(admissions, start=1):
            row_data = self._get_admission_row(admission)
            for col_index, value in enumerate(row_data):
                worksheet.write(row_index, col_index, value, cell_format)

        worksheet.set_column(0, 0, 20)
        worksheet.set_column(1, 1, 18)
        worksheet.set_column(2, 2, 28)
        worksheet.set_column(3, 3, 32)
        worksheet.set_column(4, 10, 18)

        workbook.close()
        output.seek(0)

        excel_base64 = base64.b64encode(output.read()).decode()
        filename = self._build_export_filename('xlsx')

        self.write({
            'excel_file': excel_base64,
            'excel_filename': filename,
            'state': 'done',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'batch.csv.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }
