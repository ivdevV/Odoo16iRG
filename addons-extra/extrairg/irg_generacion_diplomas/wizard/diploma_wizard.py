from odoo import models, fields, api, _, modules
from babel.dates import format_date
import base64
import os

class DiplomaWizard(models.TransientModel):
    _name = 'irg.diploma.wizard'
    _description = 'Asistente de Generación de Diplomas'

    def _default_student(self):
        return self.env.context.get('active_id')

    student_id = fields.Many2one('op.student', string='Estudiante', default=_default_student, required=True, readonly=True)
    student_course_id = fields.Many2one('op.student.course', string='Curso Completado', required=True, 
                                        domain="[('student_id', '=', student_id)]")
    
    diploma_type = fields.Selection([
        ('digital', 'Digital (Con Logo)'),
        ('physical', 'Físico (Sin Logo)')
    ], string='Tipo de Diploma', default='digital', required=True)
    
    date = fields.Date(string='Fecha de Expedición', default=fields.Date.context_today, required=True)
    
    def _get_formatted_date(self, date_obj, locale='es_ES'):
        # Format: 20 de enero de 2026
        return format_date(date_obj, format='d MMMM y', locale=locale)

    def _get_image_data(self, image_name):
        """ Returns base64 string of the image or None """
        try:
            image_path = modules.get_module_resource('irg_generacion_diplomas', 'static/src/img', image_name)
            if image_path and os.path.exists(image_path):
                with open(image_path, "rb") as image_file:
                    return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            return None
        return None

    def action_print_diploma(self):
        self.ensure_one()
        # Get or create sequence
        registry_number = self.env['ir.sequence'].next_by_code('irg.diploma.registry') or 'DRAFT'
        
        # Format dates
        # Spanish: 18 de noviembre de 2025
        # Catalan: 18 de novembre de 2025
        date_es = "{} de {} de {}".format(self.date.day, format_date(self.date, format='MMMM', locale='es_ES'), self.date.year)
        date_cat = "{} de {} de {}".format(self.date.day, format_date(self.date, format='MMMM', locale='ca_ES'), self.date.year)

        # Names
        # For student, we prefer Title Case if not already
        student_name = self.student_id.search([('id','=',self.student_id.id)]).name or ""
        
        course_name_es = self.student_course_id.course_id.name
        course_name_cat = self.student_course_id.course_id.name_cat or course_name_es

        # QR URL
        # https://institutoraimongaja.com/verificar/?id=CODIGO_REGISTRO
        qr_url = "https://institutoraimongaja.com/verificar/?id={}".format(registry_number)

        # Load images as base64 to avoid wkhtmltopdf path issues
        bg_image = self._get_image_data('digital_bg.png')
        logo_img = self._get_image_data('logo_irg.png')
        sign_raimon = self._get_image_data('firma_raimon.png')
        sign_grecia = self._get_image_data('firma_grecia.png')

        data = {
            'form': {
                'student_name': student_name,
                'course_name_es': course_name_es,
                'course_name_cat': course_name_cat,
                'diploma_type': self.diploma_type,
                'date_es': date_es,
                'date_cat': date_cat,
                'registry_number': registry_number,
                'qr_url': qr_url,
                'bg_image': bg_image,
                'logo_img': logo_img,
                'sign_raimon': sign_raimon,
                'sign_grecia': sign_grecia,
            }
        }
        
        if self.diploma_type == 'physical':
             return self.env.ref('irg_generacion_diplomas.action_report_diploma_physical').report_action(self, data=data)
        else:
             return self.env.ref('irg_generacion_diplomas.action_report_diploma').report_action(self, data=data)
