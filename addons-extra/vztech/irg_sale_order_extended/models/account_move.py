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

        for move in moves_with_pay_date:
            ref_date = fields.Date.to_date(move.payment_date)
            orig_invoice_date = move.invoice_date
            try:
                move.invoice_date = ref_date
                super(AccountMove, move)._compute_needed_terms()
            finally:
                move.invoice_date = orig_invoice_date

        other_moves = self - moves_with_pay_date
        if other_moves:
            super(AccountMove, other_moves)._compute_needed_terms()
