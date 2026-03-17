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
        que el pago se complete exitosamente.

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
                order.sudo().write({
                    'stripe_subscription_ref': tx.token_id.provider_ref or tx.reference,
                })

                # Sync Stripe Customer ID to partner
                if tx.token_id.provider_ref and not order.partner_id.irg_stripe_customer_id:
                    order.partner_id.sudo().write({
                        'irg_stripe_customer_id': tx.token_id.provider_ref,
                    })

                _logger.info(
                    "IRG Stripe: Token %s (provider=%s) asignado a "
                    "suscripción %s tras transacción %s",
                    tx.token_id.id,
                    tx.token_id.provider_id.name,
                    order.name,
                    tx.reference,
                )

        return res
