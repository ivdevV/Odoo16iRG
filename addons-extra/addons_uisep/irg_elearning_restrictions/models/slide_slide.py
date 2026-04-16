from odoo import models, fields, api, _
from odoo.exceptions import AccessError

class Slide(models.Model):
    _inherit = 'slide.slide'

    restriction_slide_ids = fields.Many2many(
        'slide.slide',
        'slide_restriction_rel',
        'slide_id',
        'required_slide_id',
        string='Diapositivas Requisito',
        help='Diapositivas que deben completarse antes de acceder a esta.',
        domain="[('channel_id', '=', channel_id), ('id', '!=', id)]",
    )

    def _check_prerequisite(self):
        """ Check if the user has completed the prerequisite slides. """
        pass
        # La restricción se maneja ahora en el controlador web (controllers/main.py)
        # para dar una mejor experiencia de usuario.

    # def read(self, fields=None, load='_classic_read'):
    #     # Desactivamos la restricción en backend para evitar problemas de administración
    #     return super(Slide, self).read(fields=fields, load=load)



