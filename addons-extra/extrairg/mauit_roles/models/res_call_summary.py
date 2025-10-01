# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResCallSummary(models.Model):
    _inherit = "res.call.summary"

    partner_id = fields.Many2one(
        "res.partner",
        string="Contacto lead",
        compute="_compute_partner_id",
        search="_search_partner_id",
    )

    @api.model
    def _search_partner_id(self, operator, value):
        return [("crm_lead_id.partner_id", operator, value)]
