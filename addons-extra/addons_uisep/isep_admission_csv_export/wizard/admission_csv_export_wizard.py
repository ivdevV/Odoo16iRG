# -*- coding: utf-8 -*-

import base64
import csv
import io
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AdmissionCsvExportWizard(models.TransientModel):
    _name = 'admission.csv.export.wizard'
    _description = 'Wizard para exportar admisiones a CSV'

    admission_ids = fields.Many2many('op.admission', string='Admisiones')
    admission_count = fields.Integer(string='Cantidad de admisiones', compute='_compute_admission_count')
    csv_file = fields.Binary(string='Archivo CSV', readonly=True)
    csv_filename = fields.Char(string='Nombre del archivo')
    state = fields.Selection([
        ('choose', 'Elegir'),
        ('done', 'Hecho')
    ], default='choose', string='Estado')

    @api.depends('admission_ids')
    def _compute_admission_count(self):
        for record in self:
            record.admission_count = len(record.admission_ids)

    @api.model
    def default_get(self, fields_list):
        res = super(AdmissionCsvExportWizard, self).default_get(fields_list)
        active_ids = self.env.context.get('active_ids', [])
        if active_ids:
            res['admission_ids'] = [(6, 0, active_ids)]
        return res

    def _get_csv_headers(self):
        """Define los encabezados del CSV"""
        return [
            'Número de Aplicación',
            'Título',
            'Nombre',
            'Fecha de Admisión',
            'Fecha de Aplicación',
            'Curso',
            'Lote',
            'Estado',
            'Bienvenida',
        ]

    def _get_admission_row(self, admission):
        """Obtiene una fila de datos para una admisión"""
        # Título
        title = ''
        if admission.title:
            title = admission.title.name or ''
        
        # Estado
        state = ''
        if admission.state:
            state = dict(admission._fields['state'].selection).get(admission.state, '')
        
        # Bienvenida
        bienvenida = ''
        if hasattr(admission, 'welcome_email_sent'):
            bienvenida = 'Sí' if admission.welcome_email_sent else 'No'
        elif hasattr(admission, 'bienvenida'):
            bienvenida = 'Sí' if admission.bienvenida else 'No'

        return [
            admission.application_number or '',
            title,
            admission.name or '',
            admission.admission_date.strftime('%d/%m/%Y') if admission.admission_date else '',
            admission.application_date.strftime('%d/%m/%Y %H:%M:%S') if admission.application_date else '',
            admission.course_id.name if admission.course_id else '',
            admission.batch_id.name if admission.batch_id else '',
            state,
            bienvenida,
        ]

    def action_export_csv(self):
        """Genera el archivo CSV con las admisiones seleccionadas"""
        self.ensure_one()
        
        if not self.admission_ids:
            raise UserError(_('No se han seleccionado admisiones para exportar.'))
        
        # Crear el CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        
        # Escribir encabezados
        writer.writerow(self._get_csv_headers())
        
        # Escribir datos
        for admission in self.admission_ids:
            writer.writerow(self._get_admission_row(admission))
        
        # Convertir a base64 con BOM para Excel
        csv_content = output.getvalue()
        csv_bytes = csv_content.encode('utf-8-sig')
        csv_base64 = base64.b64encode(csv_bytes).decode()
        
        # Actualizar el wizard
        filename = f"admisiones_{fields.Date.today().strftime('%Y%m%d')}.csv"
        self.write({
            'csv_file': csv_base64,
            'csv_filename': filename,
            'state': 'done',
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'admission.csv.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }
