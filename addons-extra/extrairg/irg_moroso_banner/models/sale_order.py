# -*- coding: utf-8 -*-

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    _IRG_MOROSO_TRIGGER_FIELDS = frozenset({
        'partner_id',
        'student_id',
        'state',
    })

    def _irg_moroso_partners(self):
        return (self.partner_id | self.student_id).exists()

    def write(self, vals):
        previous_partner_ids = []
        triggered = bool(self._IRG_MOROSO_TRIGGER_FIELDS.intersection(vals))
        if triggered:
            previous_partner_ids = self._irg_moroso_partners().ids
        result = super().write(vals)
        if triggered:
            partners = self._irg_moroso_partners()
            partners |= self.env['res.partner'].browse(previous_partner_ids)
            partners.exists()._irg_recompute_moroso()
        return result
