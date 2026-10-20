# -*- coding: utf-8 -*-

from odoo import api, models


class OpStudent(models.Model):
    _inherit = 'op.student'

    @api.model_create_multi
    def create(self, vals_list):
        students = super().create(vals_list)
        students.partner_id._irg_recompute_banners()
        return students

    def write(self, vals):
        previous_partner_ids = []
        if 'partner_id' in vals:
            previous_partner_ids = self.partner_id.ids
        result = super().write(vals)
        if 'partner_id' in vals:
            partners = self.partner_id
            partners |= self.env['res.partner'].browse(previous_partner_ids)
            partners.exists()._irg_recompute_banners()
        return result
