# -*- coding: utf-8 -*-

from odoo import api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    _IRG_MOROSO_TRIGGER_FIELDS = frozenset({
        'state',
        'payment_state',
        'partner_id',
        'move_type',
        'irg_student_partner_id',
    })

    def _irg_moroso_partners(self):
        return (self.partner_id | self.irg_student_partner_id).exists()

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._irg_moroso_partners()._irg_recompute_moroso()
        return moves

    def write(self, vals):
        previous_partner_ids = []
        triggered = bool(self._IRG_MOROSO_TRIGGER_FIELDS.intersection(vals))
        if triggered:
            previous_partner_ids = (
                self.partner_id | self.irg_student_partner_id
            ).ids
        result = super().write(vals)
        if triggered:
            partners = self._irg_moroso_partners()
            partners |= self.env['res.partner'].browse(previous_partner_ids)
            partners.exists()._irg_recompute_moroso()
        return result

    def unlink(self):
        partners = self._irg_moroso_partners()
        result = super().unlink()
        partners.exists()._irg_recompute_moroso()
        return result


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    def _irg_moroso_partners(self):
        moves = self.debit_move_id.move_id | self.credit_move_id.move_id
        return moves._irg_moroso_partners()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._irg_moroso_partners()._irg_recompute_moroso()
        return records

    def unlink(self):
        partners = self._irg_moroso_partners()
        result = super().unlink()
        partners.exists()._irg_recompute_moroso()
        return result
