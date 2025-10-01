from odoo import fields, models

class OpStudent(models.Model):
    _inherit = 'op.student'
    university_id_from = fields.Many2one(related='partner_id.university_id', string='Universidad de Procedencia')
    profession_id_from = fields.Many2one(related='partner_id.profession_id', string='Profesión')
    titulacion_id_from = fields.Many2one(related='partner_id.study_type_id', string='Titulación')
