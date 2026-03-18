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

        # Post-procesamiento: asignar token Stripe a la suscripción
        for tx in self:
            # Solo procesar transacciones Stripe exitosas con token
            if tx.provider_code != 'stripe':
                continue
            if tx.state != 'done':
                continue
            if not tx.token_id:
                continue

            for order in tx.sale_order_ids:
                # Solo suscripciones
                if not order.is_subscription:
                    continue
                # No sobreescribir un token ya asignado manualmente
                if order.payment_token_id:
                    _logger.info(
                        "IRG Stripe: Suscripción %s ya tiene token %s, "
                        "no se sobreescribe con %s",
                        order.name,
                        order.payment_token_id.id,
                        tx.token_id.id,
                    )
                    continue

                order.sudo().write({
                    'payment_token_id': tx.token_id.id,
                })

                # Only set stripe_subscription_ref to token ref if NOT using native subscriptions
                # (native mode will set it to the sub_... id later)
                stripe_mode = getattr(order, 'irg_subscription_stripe_mode', False)
                if stripe_mode != 'stripe_subscription_real':
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

                # --- Crear suscripción nativa en Stripe si el modo lo requiere ---
                self._irg_maybe_create_stripe_subscription(tx, order)

        return res

    def _irg_maybe_create_stripe_subscription(self, tx, order):
        """
        If the order is configured for ``stripe_subscription_real`` mode,
        create a native Stripe Subscription after the first successful payment.
        """
        stripe_mode = getattr(order, 'irg_subscription_stripe_mode', False)
        if stripe_mode != 'stripe_subscription_real':
            return

        # Skip if a Stripe Subscription already exists (avoid duplicates)
        if order.stripe_subscription_ref and order.stripe_subscription_ref.startswith('sub_'):
            _logger.info(
                "IRG Stripe: order %s already has Stripe subscription %s, skipping",
                order.name,
                order.stripe_subscription_ref,
            )
            return

        # Extract the Stripe PaymentMethod ID from the token
        # In Odoo 16 payment_stripe:
        #   token.provider_ref          = Stripe Customer (cus_xxx)
        #   token.stripe_payment_method = Stripe PM       (pm_xxx)
        payment_method_id = tx.token_id.stripe_payment_method
        if not payment_method_id:
            _logger.warning(
                "IRG Stripe: token %s for order %s has no stripe_payment_method, "
                "cannot create Stripe Subscription",
                tx.token_id.id,
                order.name,
            )
            return

        api = self.env['irg.stripe.api']
        result = api._create_stripe_subscription(order, payment_method_id=payment_method_id)
        if result.get('id'):
            _logger.info(
                "IRG Stripe: native Subscription %s created for order %s",
                result['id'],
                order.name,
            )
            if hasattr(order, '_irg_log_bridge_event'):
                order._irg_log_bridge_event(
                    event_type='pending_real_subscription',
                    description="Stripe Subscription %s created successfully." % result['id'],
                )
        else:
            _logger.error(
                "IRG Stripe: failed to create native Subscription for order %s: %s",
                order.name,
                result,
            )
