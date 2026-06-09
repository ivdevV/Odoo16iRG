# -*- coding: utf-8 -*-

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.student_id:
            invoice_vals['irg_student_partner_id'] = self.student_id.id
        return invoice_vals
