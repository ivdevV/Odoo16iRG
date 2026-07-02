# -*- coding: utf-8 -*-
from odoo import models, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    def _phone_format(self, number, country=None, company=None, force_format='E164'):
        """Return the number exactly as input to bypass backend formatting/normalisation."""
        return number

    @api.onchange('phone', 'country_id', 'company_id')
    def _onchange_phone_validation(self):
        """Bypass the onchange validation that formats phone numbers."""
        pass

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        """Bypass the onchange validation that formats mobile numbers."""
        pass
