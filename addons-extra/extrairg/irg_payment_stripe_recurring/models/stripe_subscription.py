# -*- coding: utf-8 -*-
from odoo import models, fields

class StripeSubscription(models.Model):
    _name = 'stripe.subscription'
    _description = 'Stripe Subscription Base'

    name = fields.Char(string='Nombre', required=True)
    stripe_id = fields.Char(string='ID Suscripción Stripe', required=True, index=True)
