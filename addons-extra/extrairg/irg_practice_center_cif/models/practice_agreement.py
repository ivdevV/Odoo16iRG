# -*- coding: utf-8 -*-
from odoo import api, models

from odoo.addons.irg_practice_center_cif.cif import resolve_center_cif


class PracticeAgreement(models.Model):
    _inherit = 'practice.agreement'

    @api.model_create_multi
    def create(self, vals_list):
        explicit_vat = [bool(vals.get('center_vat')) for vals in vals_list]
        records = super().create(vals_list)
        for record, was_explicit in zip(records, explicit_vat):
            if was_explicit:
                continue
            center = record.practice_center_id
            if not center:
                continue
            resolved = resolve_center_cif(center.cif, False)
            if resolved:
                record.center_vat = resolved
        return records
