from odoo import models, fields, api, _
from odoo.exceptions import AccessError

class Slide(models.Model):
    _inherit = 'slide.slide'

    restriction_slide_id = fields.Many2one(
        'slide.slide',
        string='Diapositiva Requisito (Test)',
        help='La diapositiva que debe completarse antes de acceder a esta.'
    )

    def _check_prerequisite(self):
        """ Check if the user has completed the prerequisite slide. """
        pass
        # La restricción se maneja ahora en el controlador web (controllers/main.py)
        # para dar una mejor experiencia de usuario.

    # def read(self, fields=None, load='_classic_read'):
    #     # Desactivamos la restricción en backend para evitar problemas de administración
    #     return super(Slide, self).read(fields=fields, load=load)



