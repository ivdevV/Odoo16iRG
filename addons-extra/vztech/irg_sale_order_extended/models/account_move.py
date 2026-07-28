# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_date = fields.Datetime(string='Payment Date')

    def _compute_needed_terms(self):
        moves_with_pay_date = self.filtered(
            lambda m: m.is_invoice(include_receipts=True) and m.invoice_payment_term_id and m.payment_date
        )
        if not moves_with_pay_date:
            return super()._compute_needed_terms()

        res = {}
        for move in self:
            if move in moves_with_pay_date:
                ref_date = fields.Date.to_date(move.payment_date)
                orig_invoice_date = move.invoice_date
                try:
                    move.invoice_date = ref_date
                    move_terms = super(AccountMove, move)._compute_needed_terms()
                    res.update(move_terms)
                finally:
                    move.invoice_date = orig_invoice_date
            else:
                res.update(super(AccountMove, move)._compute_needed_terms())
        return res
