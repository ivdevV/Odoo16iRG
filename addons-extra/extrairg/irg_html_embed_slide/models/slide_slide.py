# -*- coding: utf-8 -*-
from odoo import models, fields, _
from .default_html import DEFAULT_TEST_HTML


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

    def action_load_test_template(self):
        """Carga la plantilla HTML de actividad tipo test en el campo irg_html_embed_code."""
        for slide in self:
            slide.irg_html_embed_code = DEFAULT_TEST_HTML
            slide.irg_use_html_embed = True
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Plantilla cargada. Recuerda sustituir {id} por el ID real del slide.'),
                'type': 'success',
                'sticky': True,
            },
        }
