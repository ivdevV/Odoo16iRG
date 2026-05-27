# -*- coding: utf-8 -*-

from unittest.mock import patch
from types import SimpleNamespace

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSubscriptionCheckoutLink(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create(
            {
                "name": "IRG Checkout Student",
                "email": "student.checkout@example.com",
            }
        )
        self.provider = (
            self.env["payment.provider"].sudo().search([("code", "=", "stripe")], limit=1)
        )
        if not self.provider:
            self.provider = self.env["payment.provider"].sudo().create(
                {
                    "name": "Stripe Test Checkout",
                    "code": "stripe",
                    "state": "disabled",
                    "company_id": self.env.company.id,
                }
            )
        self.token = self.env["payment.token"].sudo().create(
            {
                "provider_id": self.provider.id,
                "partner_id": self.partner.id,
                "provider_ref": "cus_checkout_123",
                "payment_details": "4242",
                "stripe_payment_method": "pm_checkout_123",
            }
        )
        self.tx = self.env["payment.transaction"].sudo().create(
            {
                "provider_id": self.provider.id,
                "reference": "IRG-CHECKOUT-TX",
                "amount": 0.0,
                "currency_id": self.env.company.currency_id.id,
                "partner_id": self.partner.id,
                "token_id": self.token.id,
                "operation": "validation",
                "state": "done",
            }
        )
        self.payment_tx = self.env["payment.transaction"].sudo().create(
            {
                "provider_id": self.provider.id,
                "reference": "IRG-CHECKOUT-PAY",
                "amount": 0.0,
                "currency_id": self.env.company.currency_id.id,
                "partner_id": self.partner.id,
                "token_id": self.token.id,
                "operation": "online_redirect",
                "state": "done",
            }
        )

    def _create_order(self, vals=None):
        values = {
            "partner_id": self.partner.id,
            "irg_subscription_stripe_mode": "stripe_subscription_real",
        }
        if vals:
            values.update(vals)
        return self.env["sale.order"].create(values)

    def test_generating_token_and_url(self):
        order = self._create_order()
        self.assertFalse(order.irg_subscription_checkout_token)

        order.action_irg_generate_subscription_checkout_link()

        self.assertTrue(order.irg_subscription_checkout_token)
        self.assertIn(
            "/irg/subscription/checkout/%s/" % order.id,
            order.irg_subscription_checkout_url,
        )

    def test_mail_template_renders_public_checkout_url(self):
        order = self._create_order()
        order.action_irg_generate_subscription_checkout_link()
        template = self.env.ref(
            "irg_subscription_checkout_link.mail_template_subscription_checkout_link"
        )

        body = template._render_field("body_html", [order.id])[order.id]

        self.assertIn(order.irg_subscription_checkout_url, body)
        self.assertNotIn("{{ object.irg_subscription_checkout_url }}", body)
        self.assertNotIn("{{ object.partner_id.name", body)

    def test_invalid_token_false(self):
        order = self._create_order()
        order.action_irg_generate_subscription_checkout_link()

        self.assertFalse(order._irg_validate_subscription_checkout_token("bad-token"))

    def test_future_due_uses_setup_only_in_auto_mode(self):
        future = fields.Date.add(fields.Date.today(), days=15)
        order = self._create_order({"start_date": future})

        self.assertEqual(
            order.irg_subscription_checkout_effective_mode,
            "setup_only",
        )

    def test_past_or_today_due_uses_initial_payment_in_auto_mode(self):
        today = fields.Date.today()
        order = self._create_order({"start_date": today})

        self.assertEqual(
            order.irg_subscription_checkout_effective_mode,
            "initial_payment",
        )

    def test_callback_does_not_confirm_draft_order(self):
        order = self._create_order({"irg_subscription_checkout_mode": "setup_only"})

        order._irg_checkout_assign_token_callback(self.tx)

        self.assertEqual(order.state, "draft")

    def test_callback_returns_true_when_pending_token_was_recorded(self):
        order = self._create_order({"irg_subscription_checkout_mode": "setup_only"})

        result = order._irg_checkout_assign_token_callback(self.tx)

        self.assertTrue(result)
        self.assertEqual(order.irg_pending_payment_transaction_id, self.tx)
        self.assertEqual(order.irg_pending_payment_token_id, self.token)
        self.assertEqual(
            order.irg_checkout_state,
            "tokenized_pending_confirmation",
        )

    def test_callback_returns_false_when_pending_token_was_not_recorded(self):
        order = self._create_order({"irg_subscription_checkout_mode": "setup_only"})
        invalid_token = self.token.copy(
            {
                "provider_ref": "cus_checkout_invalid_callback",
                "stripe_payment_method": False,
            }
        )
        invalid_tx = self.tx.copy(
            {
                "reference": "IRG-CHECKOUT-CALLBACK-INVALID",
                "token_id": invalid_token.id,
            }
        )

        result = order._irg_checkout_assign_token_callback(invalid_tx)

        self.assertFalse(result)
        self.assertFalse(order.irg_pending_payment_transaction_id)
        self.assertFalse(order.irg_pending_payment_token_id)
        self.assertEqual(order.irg_checkout_state, "draft")

    def test_record_pending_token_state(self):
        order = self._create_order({"irg_subscription_checkout_mode": "setup_only"})

        order._irg_record_checkout_transaction(self.tx)

        self.assertEqual(order.irg_pending_payment_token_id, self.token)
        self.assertEqual(
            order.irg_checkout_state,
            "tokenized_pending_confirmation",
        )

    def test_callback_rejects_unfinished_transaction(self):
        order = self._create_order({"irg_subscription_checkout_mode": "setup_only"})
        pending_tx = self.tx.copy({"reference": "IRG-CHECKOUT-PENDING", "state": "pending"})

        result = order._irg_record_checkout_transaction(pending_tx)

        self.assertFalse(result)
        self.assertFalse(order.irg_pending_payment_transaction_id)
        self.assertEqual(order.irg_checkout_state, "draft")

    def test_callback_rejects_token_without_stripe_payment_method(self):
        order = self._create_order({"irg_subscription_checkout_mode": "setup_only"})
        token = self.token.copy(
            {
                "provider_ref": "cus_checkout_without_pm",
                "stripe_payment_method": False,
            }
        )
        tx = self.tx.copy(
            {
                "reference": "IRG-CHECKOUT-WITHOUT-PM",
                "token_id": token.id,
            }
        )

        result = order._irg_record_checkout_transaction(tx)

        self.assertFalse(result)
        self.assertFalse(order.irg_pending_payment_transaction_id)
        self.assertFalse(order.irg_pending_payment_token_id)

    def test_checkout_token_invalid_after_pending_transaction(self):
        order = self._create_order({"irg_subscription_checkout_mode": "setup_only"})
        order.action_irg_generate_subscription_checkout_link()
        token = order.irg_subscription_checkout_token

        order._irg_record_checkout_transaction(self.tx)

        self.assertFalse(order._irg_validate_subscription_checkout_token(token))

    def test_callback_on_confirmed_order_does_not_consume_or_create_stripe(self):
        order = self._create_order({"irg_subscription_checkout_mode": "setup_only"})
        order.sudo().write({"state": "sale"})

        with patch.object(
            type(order),
            "_irg_create_stripe_subscription",
            autospec=True,
            return_value="sub_should_not_be_created",
        ) as create_mock:
            order._irg_checkout_assign_token_callback(self.tx)

        create_mock.assert_not_called()
        self.assertFalse(order.payment_token_id)
        self.assertEqual(
            order.irg_checkout_state,
            "tokenized_pending_confirmation",
        )

    def test_consuming_pending_token_assigns_payment_token_id(self):
        order = self._create_order()
        order.sudo().write(
            {
                "state": "sale",
                "irg_pending_payment_token_id": self.token.id,
                "irg_pending_payment_transaction_id": self.tx.id,
            }
        )

        with patch.object(
            type(order),
            "_irg_create_stripe_subscription",
            autospec=True,
            return_value=False,
        ):
            order._irg_consume_pending_subscription_checkout()

        self.assertEqual(order.payment_token_id, self.token)
        self.assertIn(order, self.tx.sale_order_ids)
        self.assertEqual(order.irg_checkout_state, "consumed")

    def test_existing_subscription_skips_create(self):
        order = self._create_order()
        order.sudo().write(
            {
                "state": "sale",
                "stripe_subscription_id": "sub_existing_123",
                "irg_pending_payment_token_id": self.token.id,
            }
        )

        with patch.object(
            type(order),
            "_irg_create_stripe_subscription",
            autospec=True,
            return_value=False,
        ) as create_mock:
            order._irg_consume_pending_subscription_checkout()

        create_mock.assert_not_called()

    def test_sale_done_with_pending_creates_once(self):
        order = self._create_order()
        order.sudo().write(
            {
                "state": "sale",
                "irg_pending_payment_token_id": self.token.id,
                "irg_pending_payment_transaction_id": self.tx.id,
            }
        )

        with patch.object(
            type(order),
            "_irg_create_stripe_subscription",
            autospec=True,
            return_value="sub_created_123",
        ) as create_mock:
            order._irg_consume_pending_subscription_checkout()
            order._irg_consume_pending_subscription_checkout()

        create_mock.assert_called_once_with(order)
        self.assertEqual(order.irg_checkout_state, "consumed")

    def test_setup_only_transaction_forces_tokenization_requested(self):
        from odoo.addons.irg_subscription_checkout_link.controllers.main import (
            IRGSubscriptionCheckoutController,
        )

        order = self._create_order({"irg_subscription_checkout_mode": "setup_only"})
        controller = IRGSubscriptionCheckoutController()
        captured = {}

        def _capture_create_transaction(**kwargs):
            captured["kwargs"] = kwargs
            return SimpleNamespace(_get_processing_values=lambda: {})

        with patch(
            "odoo.addons.irg_subscription_checkout_link.controllers.main.request",
            SimpleNamespace(env=self.env),
        ), patch.object(
            type(controller),
            "_get_checkout_order",
            autospec=True,
            return_value=(order, True),
        ), patch.object(
            type(controller),
            "_get_stripe_checkout_providers",
            autospec=True,
            return_value=self.provider,
        ), patch.object(
            controller,
            "_create_transaction",
            side_effect=_capture_create_transaction,
        ):
            controller.irg_subscription_checkout_transaction(
                order.id,
                "valid-token",
                payment_option_id=self.provider.id,
                flow="direct",
            )

        self.assertTrue(captured["kwargs"]["is_validation"])
        self.assertTrue(captured["kwargs"]["tokenization_requested"])
