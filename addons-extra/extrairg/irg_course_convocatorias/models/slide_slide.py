from odoo import fields, models


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    irg_content_modality = fields.Selection(
        selection=[('homeclass', 'HomeClass'), ('online', 'Online')],
        string='Modalidad iRG',
        index=True,
        help='Permite separar el contenido del curso entre HomeClass y Online dentro del mismo canal.',
    )