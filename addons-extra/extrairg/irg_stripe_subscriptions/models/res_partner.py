# -*- coding: utf-8 -*-
from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    stripe_customer_id = fields.Char(
        related='irg_stripe_customer_id',
        store=True,
        readonly=False,
        index=True,
        string='Stripe Customer ID',
        help="Mismo valor que irg_stripe_customer_id del módulo de pagos recurrentes, para compatibilidad."
    )

    stripe_subscription_ids = fields.One2many(
        'stripe.subscription',
        'partner_id',
        string='Suscripciones Stripe'
    )

    stripe_payment_link_ids = fields.Many2many(
        'stripe.payment.link',
        'partner_stripe_payment_link_rel',
        'partner_id',
        'payment_link_id',
        string='Enlaces de Pago Stripe'
    )
