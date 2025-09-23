# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64

_logger = logging.getLogger(__name__)


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    html_embed_code = fields.Text("Código HTML embebido", copy=False, translate=True)
    use_html_embed = fields.Boolean("Usar HTML embebido", compute="_compute_use_html_embed", store=True)


    @api.depends('html_embed_code')
    def _compute_use_html_embed(self):
        for slide in self:
            slide.use_html_embed = bool(slide.html_embed_code and slide.html_embed_code.strip())