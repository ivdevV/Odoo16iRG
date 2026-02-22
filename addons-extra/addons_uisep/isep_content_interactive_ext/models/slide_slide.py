# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    html_code_text = fields.Text("Código en texto plano ", copy=False, translate=True)
