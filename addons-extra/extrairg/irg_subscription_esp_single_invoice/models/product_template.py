from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    irg_subscription_billing_strategy = fields.Selection(
        selection=[
            ("legacy_installments", "Legacy installments"),
            ("single_invoice_schedule", "Single invoice + payment schedule"),
        ],
        string="IRG Subscription Billing Strategy",
        default="legacy_installments",
        help="Defines whether recurring subscriptions keep the legacy installment invoicing flow or use the new single invoice Spanish accounting strategy.",
    )
    irg_subscription_stripe_mode = fields.Selection(
        selection=[
            ("tokenized_charge", "Tokenized charge"),
            ("payment_link_fallback", "Payment link fallback"),
            ("stripe_subscription_real", "Stripe subscription real"),
        ],
        string="IRG Stripe Mode",
        default="tokenized_charge",
        help="Operational Stripe mode to be propagated to new subscription orders.",
    )
    irg_payment_link_fallback_enabled = fields.Boolean(
        string="IRG Payment Link Fallback",
        default=True,
        help="When enabled, the order may reuse the existing invoice payment-link flow as fallback for failed recurring payments.",
    )