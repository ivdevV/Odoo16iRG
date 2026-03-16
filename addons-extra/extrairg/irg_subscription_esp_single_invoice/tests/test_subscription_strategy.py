from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSubscriptionStrategy(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create({"name": "Test Subscription Partner"})
        self.product_tmpl = self.env["product.template"].create(
            {
                "name": "Test Recurring Product",
                "type": "service",
                "sale_ok": True,
                "recurring_invoice": True,
                "irg_subscription_billing_strategy": "single_invoice_schedule",
                "irg_subscription_stripe_mode": "stripe_subscription_real",
                "irg_payment_link_fallback_enabled": True,
            }
        )
        self.product = self.product_tmpl.product_variant_id

    def test_order_configuration_is_synced_from_recurring_lines(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "name": self.product.display_name,
                            "product_uom_qty": 1.0,
                            "price_unit": 120.0,
                        },
                    )
                ],
            }
        )

        order._irg_sync_subscription_configuration_from_lines()

        self.assertEqual(order.irg_subscription_billing_strategy, "single_invoice_schedule")
        self.assertEqual(order.irg_subscription_stripe_mode, "stripe_subscription_real")
        self.assertTrue(order.irg_payment_link_fallback_enabled)

    def test_temporary_adjustment_only_updates_future_unpaid_installments(self):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "irg_subscription_billing_strategy": "single_invoice_schedule",
            }
        )
        today = fields.Date.today()
        schedules = self.env["sale.subscription.schedule"]
        for index in range(3):
            schedules |= self.env["sale.subscription.schedule"].create(
                {
                    "order_id": order.id,
                    "term_number": index + 1,
                    "term_label": "%02d de 03" % (index + 1),
                    "date_due": today + timedelta(days=(index + 1) * 30),
                    "date_schedule": today + timedelta(days=(index + 1) * 30),
                    "amount_recurring_taxinc": 100.0,
                }
            )

        wizard = self.env["irg.subscription.adjustment.wizard"].create(
            {
                "sale_order_id": order.id,
                "percentage": 20.0,
                "installment_count": 2,
                "effective_date": today,
            }
        )
        wizard.action_apply()

        schedules.invalidate_recordset(["amount_recurring_taxinc", "irg_original_amount_recurring_taxinc"])
        self.assertEqual(schedules[0].amount_recurring_taxinc, 80.0)
        self.assertEqual(schedules[1].amount_recurring_taxinc, 80.0)
        self.assertEqual(schedules[2].amount_recurring_taxinc, 100.0)
        self.assertEqual(schedules[0].irg_original_amount_recurring_taxinc, 100.0)
        self.assertEqual(order.irg_adjustment_count, 1)