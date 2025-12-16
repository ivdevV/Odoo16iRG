from odoo import models, fields, api, _
from odoo.exceptions import AccessError

class Slide(models.Model):
    _inherit = 'slide.slide'

    restriction_slide_id = fields.Many2one(
        'slide.slide',
        string='Diapositiva Requisito (Test)',
        help='La diapositiva que debe completarse antes de acceder a esta.'
    )

    # CAMPO DUMMY: Mantenido temporalmente para evitar error en vista huerfana
    test_visibility_field = fields.Char(string='Campo Dummy (Borrar tras desinstalar)')

    def _check_prerequisite(self):
        """ Override or extend this if we were implementing the full check logic.
            For now, we just want to see the field.
        """
        pass

