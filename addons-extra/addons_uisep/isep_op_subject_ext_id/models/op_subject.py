# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class OpSubject(models.Model):
    _inherit = 'op.subject'
    
    id_elearning = fields.Integer(related='slide_channel_id.id', string='ID Elearning')
