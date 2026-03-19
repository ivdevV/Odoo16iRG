# -*- coding: utf-8 -*-

from odoo import api, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains('vat', 'country_id')
    def check_vat(self):
        # Skip heavy VAT/VIES validation during intermediate checkout steps.
        if self.env.context.get('skip_vat_vies_validation') or self.env.context.get('irg_fast_checkout'):
            return True
        return super().check_vat()
