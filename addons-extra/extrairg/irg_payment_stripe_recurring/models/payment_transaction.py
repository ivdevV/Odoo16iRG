# -*- coding: utf-8 -*-
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

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
                _logger.info(
                    "IRG Stripe: Token %s (provider=%s) asignado a "
                    "suscripción %s tras transacción %s",
                    tx.token_id.id,
                    tx.token_id.provider_id.name,
                    order.name,
                    tx.reference,
                )

        return res
