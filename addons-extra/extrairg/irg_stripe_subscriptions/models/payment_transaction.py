# -*- coding: utf-8 -*-
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _irg_maybe_create_stripe_subscription(self, tx, order):
        """
        Sobreescribimos completamente el método de irg_payment_stripe_recurring.
        NO llamamos a super() porque el método original espera que stripe_subscription_id sea Char
        y llama a .startswith() sobre él, lo que daría error AttributeError ahora que es Many2one.
        """
        stripe_mode = getattr(order, 'irg_subscription_stripe_mode', False)
        if stripe_mode not in ('stripe_subscription_real', 'payment_link_fallback'):
            return

        # Comprobamos si ya existe suscripción usando la relación Many2one
        existing_sub = order.stripe_subscription_id
        if existing_sub and existing_sub.stripe_id:
            _logger.info(
                "IRG Stripe (Override): order %s already has Stripe subscription %s, skipping",
                order.name,
                existing_sub.stripe_id,
            )
            return

        token = getattr(tx, 'token_id', False)
        payment_method_id = token.stripe_payment_method if token else False
        if stripe_mode == 'stripe_subscription_real' and not payment_method_id:
            _logger.warning(
                "IRG Stripe (Override): token/payment method missing for order %s, "
                "cannot create Stripe Subscription in real mode",
                order.name,
            )
            return

        # Creamos la suscripción en Stripe (este método en sale.order creará y vinculará stripe.subscription)
        sub_id = order._irg_create_stripe_subscription()
        if sub_id:
            vals = {}
            if 'stripe_subscription_ref' in order._fields and not order.stripe_subscription_ref:
                vals['stripe_subscription_ref'] = sub_id
            if 'irg_stripe_bridge_state' in order._fields:
                vals['irg_stripe_bridge_state'] = 'active_real_subscription'
            if vals:
                order.sudo().write(vals)

            _logger.info(
                "IRG Stripe (Override): native Subscription %s created for order %s",
                sub_id,
                order.name,
            )
        else:
            _logger.error(
                "IRG Stripe (Override): failed to create native Subscription for order %s",
                order.name,
            )
