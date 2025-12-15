from odoo import models, fields, api, _
from odoo.exceptions import AccessError

class Slide(models.Model):
    _inherit = 'slide.slide'

    # Usamos un campo Char simple para descartar problemas de relaciones
    test_visibility_field = fields.Char(
        string='Campo de Prueba (Visible?)',
        default='Si ves esto, el módulo funciona'
    )

