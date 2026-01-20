# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from babel.dates import format_date
import base64


class DiplomaWizard(models.TransientModel):
    _name = 'irg.diploma.wizard'
    _description = 'Asistente de Generacion de Diplomas'

    def _default_student(self):
        return self.env.context.get('active_id')

    student_id = fields.Many2one('op.student', string='Estudiante', default=_default_student, required=True, readonly=True)
    student_course_id = fields.Many2one('op.student.course', string='Curso Completado', required=True, 
                                        domain="[('student_id', '=', student_id)]")
    
    diploma_type = fields.Selection([
        ('digital', 'Digital (Con Logo)'),
        ('physical', 'Fisico (Sin Logo)')
    ], string='Tipo de Diploma', default='digital', required=True)
    
    date = fields.Date(string='Fecha de Expedicion', default=fields.Date.context_today, required=True)

    def action_print_diploma(self):
        self.ensure_one()
        
        # Get sequence
        registry_number = self.env['ir.sequence'].next_by_code('irg.diploma.registry') or 'DRAFT'
        
        # Format dates
        date_es = "{} de {} de {}".format(
            self.date.day, 
            format_date(self.date, format='MMMM', locale='es_ES'), 
            self.date.year
        )
        date_cat = "{} de {} de {}".format(
            self.date.day, 
            format_date(self.date, format='MMMM', locale='ca_ES'), 
            self.date.year
        )

        # Get names
        student_name = self.student_id.name or ""
        course_name_es = self.student_course_id.course_id.name
        course_name_cat = getattr(self.student_course_id.course_id, 'name_cat', None) or course_name_es

        # QR URL
        qr_url = "https://institutoraimongaja.com/verificar/?id={}".format(registry_number)

        # Prepare data
        data = {
            'student_name': student_name,
            'course_name_es': course_name_es,
            'course_name_cat': course_name_cat,
            'date_es': date_es,
            'date_cat': date_cat,
            'registry_number': registry_number,
            'qr_url': qr_url,
        }
        
        # Generate PDF using reportlab
        pdf_generator = self.env['report.irg_generacion_diplomas.diploma_pdf']
        pdf_content = pdf_generator.generate_diploma_pdf(data, diploma_type=self.diploma_type)
        
        # Create attachment
        filename = "Diploma_{}_{}.pdf".format(
            student_name.replace(' ', '_'),
            self.diploma_type.capitalize()
        )
        
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': 'op.student',
            'res_id': self.student_id.id,
            'mimetype': 'application/pdf',
        })
        
        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }
