# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    irg_html_embed_code = fields.Text(
        string='Código HTML embebido',
        copy=False,
        translate=True,
        help='Pega aquí el HTML completo que se mostrará en el reproductor de la diapositiva.',
    )
    irg_use_html_embed = fields.Boolean(
        string='Usar HTML embebido',
        compute='_compute_irg_use_html_embed',
        store=True,
        help='Se activa automáticamente cuando existe código HTML embebido.',
    )

    @api.depends('irg_html_embed_code')
    def _compute_irg_use_html_embed(self):
        for slide in self:
            slide.irg_use_html_embed = bool(
                slide.irg_html_embed_code and slide.irg_html_embed_code.strip()
            )
