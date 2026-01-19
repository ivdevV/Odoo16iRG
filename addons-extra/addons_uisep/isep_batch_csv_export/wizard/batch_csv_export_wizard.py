# -*- coding: utf-8 -*-

import base64
import csv
import io
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BatchCsvExportWizard(models.TransientModel):
    _name = 'batch.csv.export.wizard'
    _description = 'Wizard para exportar estudiantes del lote a CSV'

    batch_id = fields.Many2one('op.batch', string='Lote', readonly=True)
    csv_file = fields.Binary(string='Archivo CSV', readonly=True)
    csv_filename = fields.Char(string='Nombre del archivo')
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

        return [
            admission.application_number or '',
            admission.batch_id.name if admission.batch_id else '',
            admission.name or '',
            admission.admission_date.strftime('%d/%m/%Y') if admission.admission_date else '',
            admission.application_date.strftime('%d/%m/%Y %H:%M:%S') if admission.application_date else '',
            admission.course_id.name if admission.course_id else '',
            payment_state,
            tfm,
            practicas,
            state,
        ]

    def action_export_csv(self):
        """Genera el archivo CSV con los estudiantes del lote"""
        self.ensure_one()
        
        if not self.batch_id:
            raise UserError(_('No se ha seleccionado ningún lote.'))
        
        # Buscar admisiones del lote
        admissions = self.env['op.admission'].search([
            ('batch_id', '=', self.batch_id.id),
            ('state', '=', 'done')
        ], order='application_date desc')
        
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
        filename = f"estudiantes_{self.batch_id.code or self.batch_id.name}_{fields.Date.today().strftime('%Y%m%d')}.csv"
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
