from types import SimpleNamespace
from unittest.mock import Mock, patch

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPaymentTransactionStripeRecurring(TransactionCase):
    def setUp(self):
        super().setUp()
        self.PaymentTransaction = self.env["payment.transaction"]
        self.partner = self.env["res.partner"].create(
            {"name": "Stripe Recurring Test Partner"}
        )

    def _create_order(self, stripe_mode):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "irg_subscription_stripe_mode": stripe_mode,
            }
        )

    @staticmethod
    def _make_tx(token=True, payment_method="pm_test_123", provider_ref="cus_test_123"):
        if not token:
            return SimpleNamespace(token_id=False)
        return SimpleNamespace(
            token_id=SimpleNamespace(
                id=99,
                stripe_payment_method=payment_method,
                provider_ref=provider_ref,
            )
        )

    def test_maybe_create_delegates_to_canonical_order_method_in_real_mode(self):
        order = self._create_order("stripe_subscription_real")
        tx = self._make_tx(payment_method="pm_real_123")

        with patch.object(
            type(order),
            "_irg_create_stripe_subscription",
            autospec=True,
            return_value=False,
        ) as create_mock:
            self.PaymentTransaction._irg_maybe_create_stripe_subscription(tx, order)

        create_mock.assert_called_once_with(order)

    def test_maybe_create_delegates_to_canonical_order_method_in_payment_link_mode(self):
        order = self._create_order("payment_link_fallback")
        tx = self._make_tx(token=False)

        with patch.object(
            type(order),
            "_irg_create_stripe_subscription",
            autospec=True,
            return_value=False,
        ) as create_mock:
            self.PaymentTransaction._irg_maybe_create_stripe_subscription(tx, order)

        create_mock.assert_called_once_with(order)

    def test_maybe_create_skips_when_order_already_has_subscription_ref(self):
        order = self._create_order("stripe_subscription_real")
        order.sudo().write({"stripe_subscription_ref": "sub_existing_ref"})
        tx = self._make_tx(payment_method="pm_real_123")

        with patch.object(
            type(order),
            "_irg_create_stripe_subscription",
            autospec=True,
            return_value=False,
        ) as create_mock:
            self.PaymentTransaction._irg_maybe_create_stripe_subscription(tx, order)

        create_mock.assert_not_called()

    def test_maybe_create_skips_when_order_already_has_subscription_id(self):
        order = self._create_order("payment_link_fallback")
        if "stripe_subscription_id" not in order._fields:
            self.skipTest("stripe_subscription_id field is not available in this database")
        order.sudo().write({"stripe_subscription_id": "sub_existing_id"})
        tx = self._make_tx(token=False)

        with patch.object(
            type(order),
            "_irg_create_stripe_subscription",
            autospec=True,
            return_value=False,
        ) as create_mock:
            self.PaymentTransaction._irg_maybe_create_stripe_subscription(tx, order)

        create_mock.assert_not_called()

    def test_maybe_create_skips_real_mode_without_token(self):
        order = self._create_order("stripe_subscription_real")
        tx = self._make_tx(token=False)

        with patch.object(
            type(order),
            "_irg_create_stripe_subscription",
            autospec=True,
            return_value=False,
        ) as create_mock:
            self.PaymentTransaction._irg_maybe_create_stripe_subscription(tx, order)

        create_mock.assert_not_called()

    def test_maybe_create_skips_real_mode_without_payment_method(self):
        order = self._create_order("stripe_subscription_real")
        tx = self._make_tx(payment_method=False)

        with patch.object(
            type(order),
            "_irg_create_stripe_subscription",
            autospec=True,
            return_value=False,
        ) as create_mock:
            self.PaymentTransaction._irg_maybe_create_stripe_subscription(tx, order)

        create_mock.assert_not_called()

    def test_maybe_create_keeps_bridge_state_coherent_after_canonical_creation(self):
        order = self._create_order("stripe_subscription_real")
        if "irg_stripe_bridge_state" in order._fields:
            order.sudo().write({"irg_stripe_bridge_state": "pending_real_subscription"})
        tx = self._make_tx(payment_method="pm_real_123")

        def fake_create(order_record):
            vals = {"stripe_subscription_ref": "sub_created_123"}
            if "stripe_subscription_id" in order_record._fields:
                vals["stripe_subscription_id"] = "sub_created_123"
            if "stripe_subscription_state" in order_record._fields:
                vals["stripe_subscription_state"] = "active"
            order_record.sudo().write(vals)
            return "sub_created_123"

        with patch.object(
            type(order),
            "_irg_create_stripe_subscription",
            autospec=True,
            side_effect=fake_create,
        ) as create_mock, patch.object(
            type(order),
            "_irg_log_bridge_event",
            autospec=True,
        ) as log_mock:
            self.PaymentTransaction._irg_maybe_create_stripe_subscription(tx, order)

        create_mock.assert_called_once_with(order)
        order.invalidate_recordset(
            ["stripe_subscription_ref", "stripe_subscription_state"]
            + (
                ["stripe_subscription_id"]
                if "stripe_subscription_id" in order._fields
                else []
            )
            + (
                ["irg_stripe_bridge_state"]
                if "irg_stripe_bridge_state" in order._fields
                else []
            )
        )
        self.assertEqual(order.stripe_subscription_ref, "sub_created_123")
        if "stripe_subscription_id" in order._fields:
            self.assertEqual(order.stripe_subscription_id, "sub_created_123")
        self.assertEqual(order.stripe_subscription_state, "active")
        if "irg_stripe_bridge_state" in order._fields:
            self.assertEqual(order.irg_stripe_bridge_state, "active_real_subscription")
        log_mock.assert_called_once()

    def test_create_subscription_uses_stable_order_idempotency_key(self):
        order = self._create_order("payment_link_fallback")
        order.partner_id.sudo().write({"irg_stripe_customer_id": "cus_existing_123"})
        order.sudo().write({"stripe_price_id": "price_existing_123"})
        provider = Mock()
        provider._stripe_make_request.return_value = {
            "id": "sub_test_123",
            "status": "active",
        }

        with patch.object(
            type(order),
            "_irg_get_stripe_provider",
            autospec=True,
            return_value=provider,
        ), patch(
            "odoo.addons.irg_payment_stripe_recurring.models.stripe_subscription_bridge.time.time",
            return_value=1712345678,
        ):
            sub_id = order._irg_create_stripe_subscription()

        self.assertEqual(sub_id, "sub_test_123")
        provider._stripe_make_request.assert_called_once()
        args, kwargs = provider._stripe_make_request.call_args
        self.assertEqual(args[0], "subscriptions")
        self.assertEqual(kwargs["idempotency_key"], "irg_sub_%s" % order.id)
