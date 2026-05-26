# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    stripe_api_key = fields.Char(
        string='Stripe Secret Key',
        config_parameter='stripe.api_key',
        help="Secret key de Stripe (sk_live_... o sk_test_...)"
    )
    
    stripe_publishable_key = fields.Char(
        string='Stripe Publishable Key',
        config_parameter='stripe.publishable_key',
        help="Publishable key de Stripe (pk_...)"
    )

    stripe_webhook_secret = fields.Char(
        string='Stripe Webhook Secret',
        config_parameter='stripe.webhook_secret',
        help="Secret de firma del Webhook (whsec_...)"
    )

    stripe_api_version = fields.Char(
        string='Stripe API Version',
        config_parameter='stripe.api_version',
        default='2025-06-30.basil',
        help="Versión fija de la API de Stripe para garantizar compatibilidad."
    )
