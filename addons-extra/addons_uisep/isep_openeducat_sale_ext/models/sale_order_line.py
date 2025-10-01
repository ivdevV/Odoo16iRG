# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    admission_status = fields.Selection(
        string=_('Estado de admisión'),
        selection=[
            ('yes', 'Admisión Website'),
            ('no', 'Sin admisión'),
        ],
        compute='_compute_admission_status'
    )

    
    @api.depends('admission_id')
    def _compute_admission_status(self):
        for record in self:
            record.admission_status = 'yes' if record.order_id.admission_id else 'no'
