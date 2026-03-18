# -*- coding: utf-8 -*-
"""
Webhook controller for native Stripe Subscription events.

Extends the base ``payment_stripe`` webhook endpoint to handle subscription-
specific event types that the standard Odoo module ignores.
"""
import logging
import pprint

from odoo import http
from odoo.http import request
from odoo.addons.payment_stripe.controllers.main import StripeController

_logger = logging.getLogger(__name__)

# Events we handle — all others fall through to the base controller
_SUBSCRIPTION_EVENTS = {
    'customer.subscription.created',
    'customer.subscription.updated',
    'customer.subscription.deleted',
    'customer.subscription.paused',
    'customer.subscription.resumed',
    'customer.subscription.pending_update_applied',
    'customer.subscription.pending_update_expired',
    'customer.subscription.trial_will_end',
    'invoice.paid',
    'invoice.payment_failed',
    'invoice.payment_action_required',
}


class IrgStripeWebhookController(StripeController):
    """
    Inherits ``/payment/stripe/webhook`` so that subscription events from
    Stripe are processed without requiring a second endpoint.
    """

    @http.route('/payment/stripe/webhook', type='json', auth='public', csrf=False)
    def stripe_webhook(self, **data):
        """
        Override the base webhook handler.  If the event is subscription-
        related, process it here; otherwise delegate to ``super()``.
        """
        event_type = data.get('type', '')

        if event_type in _SUBSCRIPTION_EVENTS:
            _logger.info(
                "IRG Stripe Subscription webhook received:\n%s",
                pprint.pformat({
                    'type': event_type,
                    'id': data.get('id'),
                    'subscription': (data.get('data', {}).get('object', {}).get('id', '')),
                }),
            )
            try:
                self._irg_handle_subscription_event(data)
            except Exception:
                _logger.exception(
                    "IRG Stripe: error processing subscription webhook %s",
                    event_type,
                )
            # Still let the base handler run for invoice.paid etc.
            # which may carry a payment_intent the base module recognizes
            if event_type.startswith('invoice.'):
                return super().stripe_webhook(**data)
            return ''

        # Non-subscription events → base handler
        return super().stripe_webhook(**data)

    # ------------------------------------------------------------------
    #  Dispatcher
    # ------------------------------------------------------------------
    def _irg_handle_subscription_event(self, data):
        event_type = data.get('type', '')
        obj = data.get('data', {}).get('object', {})

        handler_map = {
            'customer.subscription.created': self._irg_on_subscription_created,
            'customer.subscription.updated': self._irg_on_subscription_updated,
            'customer.subscription.deleted': self._irg_on_subscription_deleted,
            'customer.subscription.paused': self._irg_on_subscription_paused,
            'customer.subscription.resumed': self._irg_on_subscription_resumed,
            'invoice.paid': self._irg_on_invoice_paid,
            'invoice.payment_failed': self._irg_on_invoice_payment_failed,
        }
        handler = handler_map.get(event_type)
        if handler:
            handler(obj)

    # ------------------------------------------------------------------
    #  Find the Odoo sale.order for a Stripe Subscription ID
    # ------------------------------------------------------------------
    def _irg_find_order_by_subscription(self, subscription_id):
        if not subscription_id:
            return request.env['sale.order'].browse()
        return (
            request.env['sale.order']
            .sudo()
            .search([('stripe_subscription_ref', '=', subscription_id)], limit=1)
        )

    # ------------------------------------------------------------------
    #  Event handlers
    # ------------------------------------------------------------------
    def _irg_on_subscription_created(self, obj):
        order = self._irg_find_order_by_subscription(obj.get('id'))
        if not order:
            _logger.info("IRG Stripe webhook: subscription.created for unknown sub %s", obj.get('id'))
            return
        order._irg_mark_stripe_event(
            event_name='customer.subscription.created',
            state='active',
            clear_grace=True,
        )

    def _irg_on_subscription_updated(self, obj):
        order = self._irg_find_order_by_subscription(obj.get('id'))
        if not order:
            return
        stripe_status = obj.get('status', '')
        state_map = {
            'active': 'active',
            'past_due': 'past_due',
            'canceled': 'canceled',
            'unpaid': 'past_due',
            'paused': 'paused',
            'trialing': 'active',
            'incomplete': 'draft',
            'incomplete_expired': 'canceled',
        }
        mapped_state = state_map.get(stripe_status)
        if mapped_state:
            order._irg_mark_stripe_event(
                event_name='customer.subscription.updated',
                state=mapped_state,
                clear_grace=(mapped_state == 'active'),
            )

    def _irg_on_subscription_deleted(self, obj):
        order = self._irg_find_order_by_subscription(obj.get('id'))
        if not order:
            return
        order._irg_mark_stripe_event(
            event_name='customer.subscription.deleted',
            state='canceled',
            clear_grace=True,
        )
        order.sudo().write({'subscription_suspended': True})

    def _irg_on_subscription_paused(self, obj):
        order = self._irg_find_order_by_subscription(obj.get('id'))
        if not order:
            return
        order._irg_mark_stripe_event(
            event_name='customer.subscription.paused',
            state='paused',
        )
        order.sudo().write({'subscription_suspended': True})

    def _irg_on_subscription_resumed(self, obj):
        order = self._irg_find_order_by_subscription(obj.get('id'))
        if not order:
            return
        order._irg_mark_stripe_event(
            event_name='customer.subscription.resumed',
            state='active',
            clear_grace=True,
        )
        order.sudo().write({'subscription_suspended': False})

    def _irg_on_invoice_paid(self, obj):
        """
        Handle ``invoice.paid`` for subscription invoices.
        Mark the corresponding schedule line as paid if identifiable.
        """
        subscription_id = obj.get('subscription')
        if not subscription_id:
            return  # Not a subscription invoice — base handles it
        order = self._irg_find_order_by_subscription(subscription_id)
        if not order:
            return
        order._irg_mark_stripe_event(
            event_name='invoice.paid',
            state='active',
            clear_grace=True,
        )
        # Mark the oldest unpaid schedule line as paid
        unpaid = order.subscription_schedule.filtered(
            lambda s: s.payment_state == 'not_paid'
        ).sorted('date_due')
        if unpaid:
            unpaid[0].sudo().write({'payment_state': 'paid'})
            _logger.info(
                "IRG Stripe webhook: marked schedule %s as paid for order %s",
                unpaid[0].id,
                order.name,
            )

    def _irg_on_invoice_payment_failed(self, obj):
        subscription_id = obj.get('subscription')
        if not subscription_id:
            return
        order = self._irg_find_order_by_subscription(subscription_id)
        if not order:
            return

        from datetime import timedelta
        from odoo import fields as odoo_fields
        grace_days = int(
            request.env['ir.config_parameter']
            .sudo()
            .get_param('irg_stripe.overdue_grace_days', '15')
        )
        grace_until = odoo_fields.Date.today() + timedelta(days=grace_days)
        order._irg_mark_stripe_event(
            event_name='invoice.payment_failed',
            state='past_due',
            grace_until=grace_until,
        )
