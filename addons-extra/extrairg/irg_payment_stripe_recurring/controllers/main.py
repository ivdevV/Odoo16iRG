# -*- coding: utf-8 -*-
"""
Stripe Subscription Webhook Controller
========================================
Receives Stripe webhook events related to subscriptions and updates the
corresponding ``sale.order`` records in Odoo.

Stripe must be configured to send events to::

    https://<your-domain>/payment/stripe/subscription/webhook

The endpoint verifies the webhook signature using the provider's
``stripe_webhook_secret``.
"""
import hashlib
import hmac
import json
import logging
import time

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

# Stripe subscription events we care about
_SUBSCRIPTION_EVENTS = {
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
    "customer.subscription.paused",
    "customer.subscription.resumed",
    "customer.subscription.pending_update_applied",
    "customer.subscription.pending_update_expired",
    "customer.subscription.trial_will_end",
    "invoice.paid",
    "invoice.payment_failed",
    "invoice.payment_action_required",
}


class IrgStripeSubscriptionWebhook(http.Controller):

    @http.route(
        "/payment/stripe/subscription/webhook",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def stripe_subscription_webhook(self):
        """Handle Stripe subscription webhook events.

        Verifies the webhook signature and dispatches to the appropriate
        handler based on the event type.
        """
        payload_bytes = request.httprequest.get_data()
        sig_header = request.httprequest.headers.get("Stripe-Signature", "")

        if not payload_bytes or not sig_header:
            _logger.warning("IRG Stripe Webhook: Missing payload or signature.")
            return {"status": "ignored"}

        # Find the Stripe provider
        provider = (
            request.env["payment.provider"]
            .sudo()
            .search([("code", "=", "stripe"), ("state", "!=", "disabled")], limit=1)
        )
        if not provider:
            _logger.error("IRG Stripe Webhook: No active Stripe provider found.")
            return {"status": "error", "message": "No Stripe provider"}

        # Verify signature
        webhook_secret = provider.stripe_webhook_secret
        if webhook_secret:
            if not self._verify_signature(payload_bytes, sig_header, webhook_secret):
                _logger.warning("IRG Stripe Webhook: Invalid signature.")
                return {"status": "error", "message": "Invalid signature"}

        try:
            event = json.loads(payload_bytes)
        except (json.JSONDecodeError, ValueError):
            _logger.error("IRG Stripe Webhook: Invalid JSON payload.")
            return {"status": "error", "message": "Invalid JSON"}

        event_type = event.get("type", "")
        event_id = event.get("id", "")

        if event_type not in _SUBSCRIPTION_EVENTS:
            _logger.debug(
                "IRG Stripe Webhook: Ignoring event type %s (%s)", event_type, event_id
            )
            return {"status": "ignored"}

        _logger.info(
            "IRG Stripe Webhook: Processing %s (event %s)", event_type, event_id
        )

        data_object = event.get("data", {}).get("object", {})

        try:
            if event_type.startswith("customer.subscription."):
                self._handle_subscription_event(event_type, data_object)
            elif event_type.startswith("invoice."):
                self._handle_invoice_event(event_type, data_object)
        except Exception:
            _logger.exception(
                "IRG Stripe Webhook: Error processing %s (%s)", event_type, event_id
            )
            return {"status": "error"}

        return {"status": "ok"}

    # ------------------------------------------------------------------
    #  Signature verification
    # ------------------------------------------------------------------

    @staticmethod
    def _verify_signature(payload_bytes, sig_header, webhook_secret, tolerance=300):
        """Verify the Stripe-Signature header.

        Uses HMAC-SHA256 per Stripe's specification.
        """
        try:
            elements = dict(
                item.split("=", 1)
                for item in sig_header.split(",")
                if "=" in item
            )
            timestamp = elements.get("t", "")
            signatures = [
                v for k, v in elements.items() if k.startswith("v1")
            ]
            if not sig_header.count(","):
                # Parse as space-separated pairs
                pass

            # Re-parse properly — Stripe format: t=xxx,v1=yyy
            parts = sig_header.split(",")
            timestamp = ""
            signatures = []
            for part in parts:
                key, _, value = part.strip().partition("=")
                if key == "t":
                    timestamp = value
                elif key == "v1":
                    signatures.append(value)

            if not timestamp or not signatures:
                return False

            # Check timestamp tolerance
            if abs(time.time() - int(timestamp)) > tolerance:
                _logger.warning("IRG Stripe Webhook: Timestamp outside tolerance.")
                return False

            # Compute expected signature
            signed_payload = "%s.%s" % (timestamp, payload_bytes.decode("utf-8"))
            expected = hmac.new(
                webhook_secret.encode("utf-8"),
                signed_payload.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            return any(hmac.compare_digest(expected, sig) for sig in signatures)

        except Exception:
            _logger.exception("IRG Stripe Webhook: Error verifying signature.")
            return False

    # ------------------------------------------------------------------
    #  Subscription event handlers
    # ------------------------------------------------------------------

    def _handle_subscription_event(self, event_type, data):
        """Process a ``customer.subscription.*`` event."""
        sub_id = data.get("id", "")
        stripe_status = data.get("status", "")
        metadata = data.get("metadata", {})

        # Find the Odoo order by subscription ID or metadata
        order = self._find_order_by_stripe_subscription(sub_id, metadata)
        if not order:
            _logger.warning(
                "IRG Stripe Webhook: No order found for subscription %s", sub_id
            )
            return

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
            "stripe_last_event": event_type,
            "stripe_last_event_at": request.env.cr.now(),
        }

        if stripe_status:
            mapped_state = status_map.get(stripe_status)
            if mapped_state:
                vals["stripe_subscription_state"] = mapped_state

        if event_type == "customer.subscription.deleted":
            vals["stripe_subscription_state"] = "canceled"
        elif event_type == "customer.subscription.paused":
            vals["stripe_subscription_state"] = "paused"
            vals["subscription_suspended"] = True
        elif event_type == "customer.subscription.resumed":
            vals["stripe_subscription_state"] = "active"
            vals["subscription_suspended"] = False
            vals["stripe_grace_until"] = False

        # Store the subscription ID if not already set
        if sub_id and not order.stripe_subscription_id:
            vals["stripe_subscription_id"] = sub_id
            vals["stripe_subscription_ref"] = sub_id

        order.sudo().write(vals)

        # Log to chatter
        status_emoji = {
            "active": "✅",
            "past_due": "⚠️",
            "canceled": "🛑",
            "paused": "⏸️",
            "draft": "📝",
        }
        emoji = status_emoji.get(vals.get("stripe_subscription_state", ""), "ℹ️")
        order.message_post(
            body=(
                "%s <b>Stripe Webhook:</b> %s<br/>"
                "Subscription: <code>%s</code><br/>"
                "Status: <b>%s</b>"
                % (emoji, event_type, sub_id, stripe_status)
            ),
            message_type="notification",
            subtype_xmlid="mail.mt_note",
        )

        _logger.info(
            "IRG Stripe Webhook: Order %s updated from %s (sub=%s, status=%s)",
            order.name,
            event_type,
            sub_id,
            stripe_status,
        )

    def _handle_invoice_event(self, event_type, data):
        """Process ``invoice.*`` events for subscription invoices."""
        sub_id = data.get("subscription", "")
        if not sub_id:
            return  # Not a subscription invoice

        metadata = data.get("metadata", {})
        order = self._find_order_by_stripe_subscription(sub_id, metadata)
        if not order:
            _logger.debug(
                "IRG Stripe Webhook: No order for subscription invoice (sub=%s)", sub_id
            )
            return

        if event_type == "invoice.paid":
            order._irg_mark_stripe_event(
                event_name="invoice.paid",
                state="active",
                clear_grace=True,
            )
        elif event_type == "invoice.payment_failed":
            from datetime import timedelta

            grace_days = int(
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("irg_stripe.overdue_grace_days", "15")
            )
            from odoo import fields as odoo_fields

            grace_until = odoo_fields.Date.today() + timedelta(days=grace_days)
            order._irg_mark_stripe_event(
                event_name="invoice.payment_failed",
                state="past_due",
                grace_until=grace_until,
            )
        elif event_type == "invoice.payment_action_required":
            order._irg_mark_stripe_event(
                event_name="invoice.payment_action_required",
                state="past_due",
            )

    # ------------------------------------------------------------------
    #  Helper: find order by Stripe subscription ID
    # ------------------------------------------------------------------

    def _find_order_by_stripe_subscription(self, sub_id, metadata=None):
        """Find the sale.order linked to a Stripe subscription."""
        SaleOrder = request.env["sale.order"].sudo()

        if sub_id:
            order = SaleOrder.search(
                [("stripe_subscription_id", "=", sub_id)], limit=1
            )
            if order:
                return order

            # Also check stripe_subscription_ref
            order = SaleOrder.search(
                [("stripe_subscription_ref", "=", sub_id)], limit=1
            )
            if order:
                return order

        # Try metadata
        if metadata:
            odoo_order_id = metadata.get("odoo_order_id")
            if odoo_order_id:
                try:
                    order = SaleOrder.browse(int(odoo_order_id)).exists()
                    if order:
                        return order
                except (ValueError, TypeError):
                    pass

        return SaleOrder
