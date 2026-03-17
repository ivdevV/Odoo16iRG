# -*- coding: utf-8 -*-
"""
Stripe Subscription Bridge — sale.order mixin
================================================
Methods to create / update / cancel **real** Stripe Subscriptions via the
Stripe API (``POST /v1/subscriptions``).

These methods are called from ``irg_subscription_esp_single_invoice`` when
the bridge state transitions to ``pending_real_subscription`` and the order
has a valid payment token.
"""
import logging
import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrderStripeBridge(models.Model):
    _inherit = "sale.order"

    stripe_subscription_id = fields.Char(
        string="Stripe Subscription ID",
        copy=False,
        readonly=True,
        help="ID real de la suscripción en Stripe (sub_xxx).",
    )
    stripe_price_id = fields.Char(
        string="Stripe Price ID",
        copy=False,
        readonly=True,
        help="ID del precio recurrente creado en Stripe (price_xxx).",
    )

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------

    def _irg_get_stripe_provider(self):
        """Return the first active Stripe provider."""
        return (
            self.env["payment.provider"]
            .sudo()
            .search([("code", "=", "stripe"), ("state", "!=", "disabled")], limit=1)
        )

    def _irg_stripe_recurrence_to_interval(self):
        """Map Odoo recurrence to Stripe interval ``(interval, interval_count)``."""
        self.ensure_one()
        rec = self.recurrence_id
        if not rec:
            return "month", 1

        # Odoo 16 subscription recurrence uses unit + duration fields
        unit = getattr(rec, "unit", False) or "month"
        duration = getattr(rec, "duration", False) or 1

        mapping = {
            "day": "day",
            "week": "week",
            "month": "month",
            "year": "year",
        }
        return mapping.get(unit, "month"), int(duration) if duration else 1

    def _irg_compute_recurring_amount(self):
        """Return the recurring amount per period (tax included) in cents."""
        self.ensure_one()
        # Prefer schedule amounts when available
        schedules = self.subscription_schedule.sorted("date_due")
        if schedules:
            # Use the first unpaid installment amount
            unpaid = schedules.filtered(lambda s: s.payment_state == "not_paid")
            if unpaid:
                amount = unpaid[0].amount_recurring_taxinc
            else:
                amount = schedules[0].amount_recurring_taxinc
        else:
            # Fall back to recurring lines total
            recurring_lines = self.order_line.filtered(
                lambda l: not l.display_type and l.product_template_id.recurring_invoice
            )
            amount = sum(recurring_lines.mapped("price_total"))

        # Stripe expects amounts in the smallest currency unit (cents)
        currency = self.currency_id
        if currency.decimal_places == 0:
            return int(amount)
        return int(round(amount * (10 ** currency.decimal_places)))

    # ------------------------------------------------------------------
    #  Stripe Price creation
    # ------------------------------------------------------------------

    def _irg_ensure_stripe_price(self, provider=None):
        """Create a Stripe Price for the recurring subscription amount.

        Returns the Stripe Price ID (``price_xxx``) or *False*.
        """
        self.ensure_one()

        if self.stripe_price_id:
            return self.stripe_price_id

        if not provider:
            provider = self._irg_get_stripe_provider()
        if not provider:
            _logger.error("IRG Stripe: No Stripe provider found for price creation.")
            return False

        amount_cents = self._irg_compute_recurring_amount()
        if amount_cents <= 0:
            _logger.error(
                "IRG Stripe: Importe recurrente <= 0 para %s, no se crea Price.",
                self.name,
            )
            return False

        interval, interval_count = self._irg_stripe_recurrence_to_interval()
        currency_code = (self.currency_id.name or "eur").lower()

        payload = {
            "unit_amount": amount_cents,
            "currency": currency_code,
            "recurring[interval]": interval,
            "recurring[interval_count]": interval_count,
            "product_data[name]": "Suscripción %s" % self.name,
            "product_data[metadata][odoo_order_id]": str(self.id),
            "product_data[metadata][odoo_order_name]": self.name or "",
            "metadata[odoo_order_id]": str(self.id),
        }

        try:
            response = provider._stripe_make_request("prices", payload=payload)
        except Exception:
            _logger.exception(
                "IRG Stripe: Error creando Price para %s", self.name
            )
            return False

        price_id = response.get("id")
        if not price_id:
            _logger.error(
                "IRG Stripe: Respuesta sin ID al crear Price para %s: %s",
                self.name,
                response,
            )
            return False

        self.sudo().write({"stripe_price_id": price_id})
        _logger.info("IRG Stripe: Price %s creado para %s", price_id, self.name)
        return price_id

    # ------------------------------------------------------------------
    #  Stripe Subscription creation
    # ------------------------------------------------------------------

    def _irg_create_stripe_subscription(self):
        """Create a real Stripe Subscription for this order.

        Prerequisites:
        - The order is a subscription in state ``sale`` or ``done``.
        - A ``payment_token_id`` with ``stripe_payment_method`` is set.
        - ``irg_subscription_stripe_mode == 'stripe_subscription_real'``

        Returns the Stripe Subscription ID (``sub_xxx``) or *False*.
        """
        self.ensure_one()

        if self.stripe_subscription_id:
            _logger.info(
                "IRG Stripe: Suscripción %s ya tiene sub ID %s, omitiendo creación.",
                self.name,
                self.stripe_subscription_id,
            )
            return self.stripe_subscription_id

        provider = self._irg_get_stripe_provider()
        if not provider:
            _logger.error("IRG Stripe: No active Stripe provider to create subscription.")
            return False

        # 1. Ensure Stripe Customer
        partner = self.partner_id
        customer_id = partner._irg_ensure_stripe_customer(provider=provider)
        if not customer_id:
            _logger.error(
                "IRG Stripe: No se pudo obtener/crear Stripe Customer para %s",
                partner.display_name,
            )
            return False

        # 2. Get payment method from token
        token = self.payment_token_id
        if not token:
            _logger.error(
                "IRG Stripe: Suscripción %s no tiene payment_token_id asignado.",
                self.name,
            )
            return False

        payment_method_id = getattr(token, "stripe_payment_method", None)
        if not payment_method_id:
            _logger.warning(
                "IRG Stripe: Token %s no tiene stripe_payment_method, "
                "se intentará sin default_payment_method.",
                token.id,
            )

        # If the token's customer differs from ours, attach the PM to our customer
        if token.provider_ref and token.provider_ref != customer_id and payment_method_id:
            try:
                provider._stripe_make_request(
                    "payment_methods/%s/attach" % payment_method_id,
                    payload={"customer": customer_id},
                )
            except Exception:
                _logger.warning(
                    "IRG Stripe: No se pudo adjuntar PM %s al customer %s "
                    "(puede que ya esté adjuntado).",
                    payment_method_id,
                    customer_id,
                )

        # 3. Ensure Stripe Price
        price_id = self._irg_ensure_stripe_price(provider=provider)
        if not price_id:
            return False

        # 4. Build subscription payload
        payload = {
            "customer": customer_id,
            "items[0][price]": price_id,
            "items[0][quantity]": "1",
            "collection_method": "charge_automatically",
            "payment_behavior": "default_incomplete",
            "payment_settings[payment_method_types][0]": "card",
            "payment_settings[save_default_payment_method]": "on_subscription",
            "metadata[odoo_order_id]": str(self.id),
            "metadata[odoo_order_name]": self.name or "",
            "off_session": "true",
        }

        if payment_method_id:
            payload["default_payment_method"] = payment_method_id

        # Description
        description = "Odoo Suscripción %s - %s" % (
            self.name or "",
            self.partner_id.name or "",
        )
        if len(description) > 500:
            description = description[:497] + "..."
        payload["description"] = description

        # Trial end (if set on the order)
        if self.stripe_trial_end:
            trial_ts = int(time.mktime(self.stripe_trial_end.timetuple()))
            payload["trial_end"] = str(trial_ts)

        # Coupon
        if self.stripe_coupon_code:
            payload["coupon"] = self.stripe_coupon_code

        # Billing anchor — align with first schedule date if available
        schedules = self.subscription_schedule.sorted("date_due")
        if schedules and schedules[0].date_due:
            anchor_ts = int(time.mktime(schedules[0].date_due.timetuple()))
            payload["billing_cycle_anchor"] = str(anchor_ts)

        # 5. Call Stripe API
        try:
            response = provider._stripe_make_request(
                "subscriptions",
                payload=payload,
                idempotency_key="irg_sub_%s_%s" % (self.id, int(time.time())),
            )
        except Exception:
            _logger.exception(
                "IRG Stripe: Error creando suscripción para %s", self.name
            )
            return False

        sub_id = response.get("id")
        if not sub_id:
            error = response.get("error", {})
            _logger.error(
                "IRG Stripe: Respuesta sin ID al crear suscripción para %s: %s",
                self.name,
                error.get("message", response),
            )
            return False

        # 6. Store result
        stripe_status = response.get("status", "active")
        status_map = {
            "active": "active",
            "trialing": "active",
            "incomplete": "draft",
            "incomplete_expired": "canceled",
            "past_due": "past_due",
            "canceled": "canceled",
            "unpaid": "past_due",
            "paused": "paused",
        }
        vals = {
            "stripe_subscription_id": sub_id,
            "stripe_subscription_ref": sub_id,
            "stripe_subscription_state": status_map.get(stripe_status, "active"),
        }
        self.sudo().write(vals)

        _logger.info(
            "IRG Stripe: Subscription %s (status=%s) creada para %s",
            sub_id,
            stripe_status,
            self.name,
        )
        return sub_id

    # ------------------------------------------------------------------
    #  Stripe Subscription lifecycle (cancel / pause / resume)
    # ------------------------------------------------------------------

    def _irg_cancel_stripe_subscription(self, invoice_now=False):
        """Cancel the Stripe Subscription if one exists."""
        self.ensure_one()
        if not self.stripe_subscription_id:
            return True

        provider = self._irg_get_stripe_provider()
        if not provider:
            return False

        payload = {}
        if invoice_now:
            payload["invoice_now"] = "true"
            payload["prorate"] = "true"

        try:
            response = provider._stripe_make_request(
                "subscriptions/%s" % self.stripe_subscription_id,
                payload=payload,
                method="DELETE",
            )
        except Exception:
            _logger.exception(
                "IRG Stripe: Error cancelando suscripción %s",
                self.stripe_subscription_id,
            )
            return False

        if response.get("status") == "canceled":
            _logger.info(
                "IRG Stripe: Subscription %s cancelada en Stripe.",
                self.stripe_subscription_id,
            )
        return True

    def _irg_pause_stripe_subscription(self):
        """Pause the Stripe Subscription (stop invoice generation)."""
        self.ensure_one()
        if not self.stripe_subscription_id:
            return True

        provider = self._irg_get_stripe_provider()
        if not provider:
            return False

        try:
            provider._stripe_make_request(
                "subscriptions/%s" % self.stripe_subscription_id,
                payload={
                    "pause_collection[behavior]": "void",
                },
            )
        except Exception:
            _logger.exception(
                "IRG Stripe: Error pausando suscripción %s",
                self.stripe_subscription_id,
            )
            return False

        _logger.info(
            "IRG Stripe: Subscription %s pausada (collection voided).",
            self.stripe_subscription_id,
        )
        return True

    def _irg_resume_stripe_subscription(self):
        """Resume a paused Stripe Subscription."""
        self.ensure_one()
        if not self.stripe_subscription_id:
            return True

        provider = self._irg_get_stripe_provider()
        if not provider:
            return False

        try:
            # First remove pause_collection
            provider._stripe_make_request(
                "subscriptions/%s" % self.stripe_subscription_id,
                payload={
                    "pause_collection": "",
                },
            )
        except Exception:
            _logger.exception(
                "IRG Stripe: Error reanudando suscripción %s",
                self.stripe_subscription_id,
            )
            return False

        _logger.info(
            "IRG Stripe: Subscription %s reanudada.",
            self.stripe_subscription_id,
        )
        return True

    # ------------------------------------------------------------------
    #  Override manual actions to also sync with Stripe
    # ------------------------------------------------------------------

    def action_irg_create_stripe_subscription(self):
        """Manual action button to create a Stripe Subscription."""
        self.ensure_one()
        if self.stripe_subscription_id:
            raise UserError(
                _("Esta suscripción ya tiene un ID de Stripe: %s")
                % self.stripe_subscription_id
            )
        if not self.is_subscription:
            raise UserError(_("Este pedido no es una suscripción."))
        if not self.payment_token_id:
            raise UserError(
                _("No hay token de pago asignado. El cliente debe completar "
                  "un primer pago con tarjeta antes de crear la suscripción en Stripe.")
            )

        sub_id = self._irg_create_stripe_subscription()
        if not sub_id:
            raise UserError(
                _("No se pudo crear la suscripción en Stripe. "
                  "Revise los logs para más detalles.")
            )

        self.message_post(
            body=(
                "✅ <b>Suscripción Stripe creada manualmente.</b><br/>"
                "ID: <code>%s</code>" % sub_id
            ),
            message_type="notification",
            subtype_xmlid="mail.mt_note",
        )
        return True

    def action_irg_pause_subscription(self):
        for order in self.filtered(
            lambda so: so.is_subscription and so.stripe_subscription_id
        ):
            order._irg_pause_stripe_subscription()

        return super().action_irg_pause_subscription()

    def action_irg_resume_subscription(self):
        for order in self.filtered(
            lambda so: so.is_subscription and so.stripe_subscription_id
        ):
            order._irg_resume_stripe_subscription()

        return super().action_irg_resume_subscription()

    def action_irg_cancel_subscription(self):
        for order in self.filtered(
            lambda so: so.is_subscription and so.stripe_subscription_id
        ):
            order._irg_cancel_stripe_subscription()

        return super().action_irg_cancel_subscription()

    # ------------------------------------------------------------------
    #  Cron: retry pending Stripe subscriptions
    # ------------------------------------------------------------------

    @api.model
    def _cron_retry_pending_stripe_subscriptions(self):
        """Find subscriptions with ``irg_stripe_bridge_state = pending_real_subscription``
        that have a payment token, and attempt to create the Stripe Subscription.
        """
        pending = self.sudo().search([
            ("is_subscription", "=", True),
            ("irg_subscription_stripe_mode", "=", "stripe_subscription_real"),
            ("stripe_subscription_id", "=", False),
            ("payment_token_id", "!=", False),
            ("state", "in", ("sale", "done")),
        ])

        created = 0
        for order in pending:
            sub_id = order._irg_create_stripe_subscription()
            if sub_id:
                vals = {"stripe_subscription_state": "active"}
                if "irg_stripe_bridge_state" in order._fields:
                    vals["irg_stripe_bridge_state"] = "active_real_subscription"
                order.sudo().write(vals)

                if hasattr(order, "_irg_log_bridge_event"):
                    order._irg_log_bridge_event(
                        event_type="stripe_subscription_created",
                        description="Stripe Subscription %s creada por cron de reintento." % sub_id,
                    )
                created += 1

        _logger.info(
            "IRG Cron retry: %d suscripciones Stripe creadas de %d pendientes.",
            created,
            len(pending),
        )
