# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from odoo import models, fields

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def write(self, vals):
        old_states = {tx.id: tx.state for tx in self}
        res = super().write(vals)

        if 'state' not in vals:
            return res

        grace_days = int(
            self.env['ir.config_parameter'].sudo().get_param('irg_stripe.overdue_grace_days', '15')
        )
        grace_until = fields.Date.today() + timedelta(days=grace_days)

        for tx in self:
            if tx.provider_code != 'stripe':
                continue
            if old_states.get(tx.id) == tx.state:
                continue
            if not tx.sale_order_ids:
                continue

            subscription_orders = tx.sale_order_ids.filtered(lambda so: so.is_subscription)
            if not subscription_orders:
                continue

            if tx.state == 'done':
                subscription_orders._irg_mark_stripe_event(
                    event_name='invoice.payment_succeeded',
                    state='active',
                    clear_grace=True,
                )
            elif tx.state == 'error':
                subscription_orders._irg_mark_stripe_event(
                    event_name='invoice.payment_failed',
                    state='past_due',
                    grace_until=grace_until,
                )
            elif tx.state == 'cancel':
                subscription_orders._irg_mark_stripe_event(
                    event_name='customer.subscription.deleted',
                    state='canceled',
                    clear_grace=True,
                )

        return res

    def _reconcile_after_done(self):
        """
        Extiende _reconcile_after_done para asignar el token Stripe
        a la suscripción (sale.order.payment_token_id) después de
        que el pago se complete exitosamente.a

        CADENA DE HERENCIA (MRO):
        Este método se ejecuta DESPUÉS de:
          - isep_sale_subscription_extension: confirma orden + crea facturas
          - Odoo base: reconcilia transacción con factura
        Nuestro código va al FINAL (post-procesamiento).

        NO MODIFICA:
          - sale.subscription.schedule
          - create_subscription_schedule()
          - _auto_scheduled_order()
          - Ninguna vista
        """
        # Primero ejecutar toda la cadena de herencia existente
        res = super()._reconcile_after_done()

        # Post-procesamiento: asignar token Stripe y crear suscripción nativa
        for tx in self:
            if tx.provider_code != 'stripe':
                continue
            if tx.state != 'done':
                continue

            for order in tx.sale_order_ids:
                if not order.is_subscription:
                    continue

                # --- 1) Asignar token (si aún no tiene uno) ---
                if tx.token_id and not order.payment_token_id:
                    order.sudo().write({
                        'payment_token_id': tx.token_id.id,
                    })
                    stripe_mode = getattr(order, 'irg_subscription_stripe_mode', False)
                    if stripe_mode not in ('stripe_subscription_real', 'payment_link_fallback'):
                        order.sudo().write({
                            'stripe_subscription_ref': tx.token_id.provider_ref or tx.reference,
                        })
                    _logger.info(
                        "IRG Stripe: Token %s (provider=%s) asignado a "
                        "suscripción %s tras transacción %s",
                        tx.token_id.id,
                        tx.token_id.provider_id.name,
                        order.name,
                        tx.reference,
                    )
                elif tx.token_id and order.payment_token_id:
                    _logger.info(
                        "IRG Stripe: Suscripción %s ya tiene token %s, "
                        "no se sobreescribe con %s",
                        order.name,
                        order.payment_token_id.id,
                        tx.token_id.id,
                    )

                # --- 2) Crear suscripción nativa (siempre, independiente del token) ---
                self._irg_maybe_create_stripe_subscription(tx, order)

        return res

    def _irg_maybe_create_stripe_subscription(self, tx, order):
        """
        If the order is configured for ``stripe_subscription_real`` or
        ``payment_link_fallback`` mode, create a native Stripe Subscription
        after the first successful payment using the canonical ``sale.order``
        bridge method.
        """
        stripe_mode = getattr(order, 'irg_subscription_stripe_mode', False)
        if stripe_mode not in ('stripe_subscription_real', 'payment_link_fallback'):
            return

        # Skip if a Stripe Subscription already exists (avoid duplicates)
        existing_sub_id = (
            getattr(order, 'stripe_subscription_id', False)
            or order.stripe_subscription_ref
        )
        if existing_sub_id and existing_sub_id.startswith('sub_'):
            _logger.info(
                "IRG Stripe: order %s already has Stripe subscription %s, skipping",
                order.name,
                existing_sub_id,
            )
            return

        token = getattr(tx, 'token_id', False)
        payment_method_id = token.stripe_payment_method if token else False
        if stripe_mode == 'stripe_subscription_real' and not payment_method_id:
            _logger.warning(
                "IRG Stripe: token/payment method missing for order %s, "
                "cannot create Stripe Subscription in real mode",
                order.name,
            )
            return

        sub_id = order._irg_create_stripe_subscription()
        if sub_id:
            vals = {}
            if 'stripe_subscription_id' in order._fields and not order.stripe_subscription_id:
                vals['stripe_subscription_id'] = sub_id
            if 'stripe_subscription_ref' in order._fields and not order.stripe_subscription_ref:
                vals['stripe_subscription_ref'] = sub_id
            if 'irg_stripe_bridge_state' in order._fields:
                vals['irg_stripe_bridge_state'] = 'active_real_subscription'
            if vals:
                order.sudo().write(vals)

            _logger.info(
                "IRG Stripe: native Subscription %s created for order %s",
                sub_id,
                order.name,
            )
            if hasattr(order, '_irg_log_bridge_event'):
                order._irg_log_bridge_event(
                    event_type='pending_real_subscription',
                    description="Stripe Subscription %s created successfully." % sub_id,
                )
        else:
            _logger.error(
                "IRG Stripe: failed to create native Subscription for order %s: %s",
                order.name,
                sub_id,
            )
