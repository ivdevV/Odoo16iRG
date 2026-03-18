# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    irg_stripe_customer_id = fields.Char(
        string="Stripe Customer ID",
        copy=False,
        help="Native Stripe Customer ID (cus_...) used for Stripe Subscriptions.",
    )
