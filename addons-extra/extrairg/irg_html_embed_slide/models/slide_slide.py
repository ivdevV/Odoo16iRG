# -*- coding: utf-8 -*-
from odoo import models, fields


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    irg_use_html_embed = fields.Boolean(
        string='Usar HTML embebido',
        default=False,
        help='Activa esta opción para que el reproductor muestre el código HTML embebido en lugar del contenido nativo.',
    )
    irg_html_embed_code = fields.Text(
        string='Código HTML embebido',
        copy=False,
        translate=True,
        help='Pega aquí el HTML completo que se mostrará en el reproductor de la diapositiva.',
    )
