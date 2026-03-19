# -*- coding: utf-8 -*-
"""
Helper service for creating native Stripe Subscriptions via the REST API.a

Uses ``payment.provider._stripe_make_request`` from Odoo 16's
``payment_stripe`` module so we automatically inherit credentials,
error handling and logging.
"""
import logging

from odoo import models, api, fields as odoo_fields

_logger = logging.getLogger(__name__)


class IrgStripeApi(models.AbstractModel):
    _name = "irg.stripe.api"
    _description = "IRG Stripe API Helper"

    # ------------------------------------------------------------------
    #  Low level: delegate to Odoo's payment_stripe provider
    # ------------------------------------------------------------------
    @api.model
    def _get_stripe_provider(self):
        """Return the first enabled Stripe payment provider."""
        provider = (
            self.env["payment.provider"]
            .sudo()
            .search([("code", "=", "stripe"), ("state", "in", ("enabled", "test"))], limit=1)
        )
        if not provider:
            _logger.error("IRG Stripe API: no active Stripe provider found")
        return provider

    def _stripe_request(self, endpoint, payload=None, method="POST"):
        """
        Thin wrapper around ``payment.provider._stripe_make_request``.

        :param str endpoint: Stripe API path, e.g. ``"customers"``
        :param dict payload: form-encoded payload
        :param str method: HTTP verb (default POST)
        :returns: parsed JSON response dict
        """
        provider = self._get_stripe_provider()
        if not provider:
            return {}
        return provider._stripe_make_request(endpoint, payload=payload, method=method)

    # ------------------------------------------------------------------
    #  Customer
    # ------------------------------------------------------------------
    def _get_or_create_stripe_customer(self, partner):
        """
        Return the Stripe Customer ID for *partner*, creating one if needed.
        The ID is persisted on ``res.partner.irg_stripe_customer_id``.
        """
        partner = partner.sudo()
        if partner.irg_stripe_customer_id:
            return partner.irg_stripe_customer_id

        payload = {
            "email": partner.email or "",
            "name": partner.name or "",
            "metadata[odoo_partner_id]": str(partner.id),
        }
        result = self._stripe_request("customers", payload=payload)
        customer_id = result.get("id")
        if not customer_id:
            _logger.error("IRG Stripe API: failed to create customer for partner %s: %s", partner.id, result)
            return False

        partner.write({"irg_stripe_customer_id": customer_id})
        _logger.info(
            "IRG Stripe API: created customer %s for partner %s (%s)",
            customer_id,
            partner.id,
            partner.name,
        )
        return customer_id

    # ------------------------------------------------------------------
    #  Attach PaymentMethod to Customer
    # ------------------------------------------------------------------
    def _attach_payment_method_to_customer(self, customer_id, payment_method_id):
        """Attach an existing Stripe PaymentMethod to a Customer."""
        result = self._stripe_request(
            "payment_methods/%s/attach" % payment_method_id,
            payload={"customer": customer_id},
        )
        if result.get("id"):
            _logger.info(
                "IRG Stripe API: attached pm %s to customer %s",
                payment_method_id,
                customer_id,
            )
        else:
            _logger.warning(
                "IRG Stripe API: attach pm %s to customer %s returned: %s",
                payment_method_id,
                customer_id,
                result,
            )
        return result

    # ------------------------------------------------------------------
    #  Product / Price
    # ------------------------------------------------------------------
    def _get_or_create_stripe_product(self, order):
        """
        Create a Stripe Product that represents this Odoo subscription.
        Returns the Stripe product ID string.
        """
        product_name = "Suscripción %s" % order.name
        payload = {
            "name": product_name,
            "metadata[odoo_order_id]": str(order.id),
            "metadata[odoo_order_name]": order.name or "",
        }
        result = self._stripe_request("products", payload=payload)
        product_id = result.get("id")
        if not product_id:
            _logger.error("IRG Stripe API: failed to create product for order %s: %s", order.name, result)
        return product_id

    def _create_stripe_price(self, stripe_product_id, amount_cents, currency, interval="month", interval_count=1):
        """
        Create a recurring Stripe Price attached to the given product.

        :param int amount_cents: unit amount in the smallest currency unit
        :param str currency: ISO currency code, e.g. ``eur``
        :param str interval: ``day``, ``week``, ``month`` or ``year``
        :param int interval_count: number of intervals between billings
        """
        payload = {
            "product": stripe_product_id,
            "unit_amount": str(int(amount_cents)),
            "currency": currency.lower(),
            "recurring[interval]": interval,
            "recurring[interval_count]": str(interval_count),
        }
        result = self._stripe_request("prices", payload=payload)
        price_id = result.get("id")
        if not price_id:
            _logger.error("IRG Stripe API: failed to create price: %s", result)
        return price_id

    # ------------------------------------------------------------------
    #  Subscription
    # ------------------------------------------------------------------
    def _create_stripe_subscription(self, order, payment_method_id=None):
        """
        Create a native Stripe Subscription for *order*.

        Steps:
          1. Ensure Stripe Customer exists for the partner
          2. Attach PaymentMethod (from the initial checkout) to the customer
          3. Create Stripe Product + recurring Price
          4. Create the Subscription

        :param order: ``sale.order`` recordset (single)
        :param str payment_method_id: Stripe PaymentMethod id (``pm_...``)
        :returns: dict with subscription data or empty dict on failure
        """
        order.ensure_one()

        # 1) Customer
        customer_id = self._get_or_create_stripe_customer(order.partner_id)
        if not customer_id:
            return {}

        # 2) Attach payment method
        if payment_method_id:
            self._attach_payment_method_to_customer(customer_id, payment_method_id)

        # 3) Product + Price
        interval, interval_count = self._order_to_stripe_interval(order)
        installment_amount = self._get_installment_amount(order)
        currency_name = (order.currency_id.name or "eur").lower()
        amount_cents = int(round(installment_amount * 100))

        stripe_product_id = self._get_or_create_stripe_product(order)
        if not stripe_product_id:
            return {}

        stripe_price_id = self._create_stripe_price(
            stripe_product_id,
            amount_cents,
            currency_name,
            interval=interval,
            interval_count=interval_count,
        )
        if not stripe_price_id:
            return {}

        # 4) Create Subscription
        stripe_mode = getattr(order, 'irg_subscription_stripe_mode', False)
        is_send_invoice = stripe_mode == 'payment_link_fallback'

        if is_send_invoice:
            days_until_due = int(
                self.env['ir.config_parameter'].sudo().get_param(
                    'irg_stripe.payment_link_days_until_due', '10'
                )
            )
            payload = {
                "customer": customer_id,
                "items[0][price]": stripe_price_id,
                "collection_method": "send_invoice",
                "days_until_due": str(days_until_due),
                "metadata[odoo_order_id]": str(order.id),
                "metadata[odoo_order_name]": order.name or "",
            }
        else:
            payload = {
                "customer": customer_id,
                "items[0][price]": stripe_price_id,
                "default_payment_method": payment_method_id or "",
                "metadata[odoo_order_id]": str(order.id),
                "metadata[odoo_order_name]": order.name or "",
                "payment_behavior": "default_incomplete",
                "payment_settings[save_default_payment_method]": "on_subscription",
            }

        # If the first payment was already captured, skip billing this cycle
        first_schedule = order.subscription_schedule.sorted("date_due")[:1]
        if first_schedule and first_schedule.payment_state == "paid":
            payload["billing_cycle_anchor_config[month]"] = str(
                (first_schedule.date_due.month % 12) + 1
            )

        # Trial or proration — skip for send_invoice mode to avoid $0 invoice
        if order.stripe_trial_end and not is_send_invoice:
            from datetime import datetime, timezone

            trial_dt = datetime.combine(order.stripe_trial_end, datetime.min.time()).replace(tzinfo=timezone.utc)
            payload["trial_end"] = str(int(trial_dt.timestamp()))

        # Coupon
        if order.stripe_coupon_code:
            payload["coupon"] = order.stripe_coupon_code

        result = self._stripe_request("subscriptions", payload=payload)
        subscription_id = result.get("id")
        if not subscription_id:
            _logger.error(
                "IRG Stripe API: failed to create subscription for order %s: %s",
                order.name,
                result,
            )
            return result

        # Persist on sale.order
        order.sudo().write({
            "stripe_subscription_id": subscription_id,
            "stripe_subscription_ref": subscription_id,
            "stripe_subscription_state": "active",
            "stripe_last_event": "subscription.created",
            "stripe_last_event_at": odoo_fields.Datetime.now(),
        })

        _logger.info(
            "IRG Stripe API: created subscription %s for order %s (customer %s, price %s)",
            subscription_id,
            order.name,
            customer_id,
            stripe_price_id,
        )
        return result

    # ------------------------------------------------------------------
    #  Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _order_to_stripe_interval(order):
        """
        Map the Odoo subscription recurrence to a Stripe billing interval.
        Returns ``(interval, interval_count)`` tuple.
        """
        if not order.recurrence_id:
            return ("month", 1)
        # ``sale.temporal.recurrence`` uses unit / duration
        unit = getattr(order.recurrence_id, "unit", "month")
        duration = getattr(order.recurrence_id, "duration", 1)
        mapping = {
            "day": "day",
            "week": "week",
            "month": "month",
            "year": "year",
        }
        return (mapping.get(unit, "month"), int(duration) if duration else 1)

    @staticmethod
    def _get_installment_amount(order):
        """
        Return the recurring installment amount for the subscription.
        Falls back to ``amount_total / term_number`` when no schedules exist.
        """
        schedules = order.subscription_schedule.sorted("date_due")
        if schedules:
            first_unpaid = schedules.filtered(lambda s: s.payment_state != "paid")
            if first_unpaid:
                return first_unpaid[0].amount_recurring_taxinc
            return schedules[0].amount_recurring_taxinc

        if order.term_number and order.term_number > 0:
            return order.currency_id.round(order.amount_total / order.term_number)
        return order.amount_total

    # ------------------------------------------------------------------
    #  Cancel / Pause / Resume on Stripe side
    # ------------------------------------------------------------------
    def _cancel_stripe_subscription(self, subscription_id):
        """Cancel a Stripe Subscription immediately."""
        result = self._stripe_request("subscriptions/%s" % subscription_id, method="DELETE")
        _logger.info("IRG Stripe API: canceled subscription %s: %s", subscription_id, result.get("status"))
        return result

    def _pause_stripe_subscription(self, subscription_id):
        """Pause collection on a Stripe Subscription."""
        result = self._stripe_request(
            "subscriptions/%s" % subscription_id,
            payload={"pause_collection[behavior]": "void"},
        )
        _logger.info("IRG Stripe API: paused subscription %s", subscription_id)
        return result

    def _resume_stripe_subscription(self, subscription_id):
        """Resume collection on a paused Stripe Subscription."""
        result = self._stripe_request(
            "subscriptions/%s" % subscription_id,
            payload={"pause_collection": ""},
        )
        _logger.info("IRG Stripe API: resumed subscription %s", subscription_id)
        return result
