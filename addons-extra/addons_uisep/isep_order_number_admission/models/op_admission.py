# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    number_invoice_count = fields.Integer(related='order_id.overdue_invoice_count_s', string='Facturas vencidas')
