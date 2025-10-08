# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderAdmissionLine(models.Model):
    _inherit = 'sale.order.admission.line'


    @api.depends('admission_date')
    def _compute_period(self):
        for record in self:
            period = False
            if record.admission_date:
                term = self.env['op.academic.term'].search([
                    ('term_start_date', '<=', record.admission_date),
                    ('term_end_date', '>=', record.admission_date)
                ], limit=1)
                if term:
                    period = f"{term.academic_year_id.name}-{term.code}"
            record.period = period



