from odoo import models, fields, api

class Slide(models.Model):
    _inherit = 'slide.slide'

    prerequisite_slide_id = fields.Many2one(
        'slide.slide',
        string='Requisito Previo',
        help='El alumno debe completar esta diapositiva para ver el contenido actual.'
    )

    is_prerequisite_met = fields.Boolean(
        compute='_compute_prerequisite_met',
        string='Requisito Cumplido'
    )

    @api.depends('prerequisite_slide_id')
    def _compute_prerequisite_met(self):
        for slide in self:
            if not slide.prerequisite_slide_id:
                slide.is_prerequisite_met = True
                continue

            completion = self.env['slide.slide.partner'].sudo().search([
                ('slide_id', '=', slide.prerequisite_slide_id.id),
                ('partner_id', '=', self.env.user.partner_id.id),
                ('completed', '=', True)
            ])
            
            slide.is_prerequisite_met = bool(completion)
