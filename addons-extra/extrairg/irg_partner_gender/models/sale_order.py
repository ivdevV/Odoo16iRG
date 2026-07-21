# -*- coding: utf-8 -*-
from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _irg_resolve_admission_gender(self, partner=None):
        """Resolve gender for admission create: SO → partner → heuristic → 'o'."""
        self.ensure_one()
        partner = partner or self.partner_id
        if not partner:
            return self.env['res.partner']._irg_normalize_gender(self.gender) or 'o'
        return partner._irg_resolve_gender(order_gender=self.gender, write_back=True)

    def _create_or_get_admission(self, line):
        if self.partner_id:
            self._irg_resolve_admission_gender()
        return super()._create_or_get_admission(line)

    def create_admission_manual(self, admission_register_id):
        if self.partner_id:
            self._irg_resolve_admission_gender()
        return super().create_admission_manual(admission_register_id)

    def get_admision_id(self, admission_register_id):
        if self.partner_id:
            self._irg_resolve_admission_gender()
        return super().get_admision_id(admission_register_id)
