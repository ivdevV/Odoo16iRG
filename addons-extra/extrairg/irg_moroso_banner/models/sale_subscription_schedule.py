# -*- coding: utf-8 -*-

from odoo import api, models


class SaleSubscriptionSchedule(models.Model):
    _inherit = 'sale.subscription.schedule'

    _IRG_MOROSO_TRIGGER_FIELDS = frozenset({
        'date_due',
        'order_id',
        'payment_state',
    })

    def _irg_moroso_partners(self):
        orders = self.order_id
        return (orders.partner_id | orders.student_id).exists()

    @api.model_create_multi
    def create(self, vals_list):
        schedules = super().create(vals_list)
        schedules._irg_moroso_partners()._irg_recompute_moroso()
        return schedules

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

    def unlink(self):
        partners = self._irg_moroso_partners()
        result = super().unlink()
        partners.exists()._irg_recompute_moroso()
        return result
