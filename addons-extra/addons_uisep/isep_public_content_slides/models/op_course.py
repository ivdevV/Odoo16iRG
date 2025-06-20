from odoo import models, fields

class OpCourse(models.Model):
    _inherit = 'op.course'

    include_txt = fields.Boolean(string="Incluir TXT para IA", help="Genera el contenido de Elearning en txt para la IA", index=True)
    
    def sync_slides_to_txt(self, limit):
        course_ids = self.search([('include_txt','=',True)])
        for record in course_ids:
            for subject in record.subject_ids:
                subject.sync_slide_to_txt(limit)