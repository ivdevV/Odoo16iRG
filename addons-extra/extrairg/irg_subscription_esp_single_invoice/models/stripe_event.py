from odoo import fields, models


class IrgSubscriptionStripeEvent(models.Model):
    _name = "irg.subscription.stripe.event"
    _description = "IRG Subscription Stripe Event"
    _order = "create_date desc, id desc"

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Subscription",
        required=True,
        ondelete="cascade",
        index=True,
    )
    event_type = fields.Selection(
        selection=[
            ("single_invoice_created", "Single invoice created"),
            ("single_invoice_linked", "Single invoice linked"),
            ("payment_link_prepared", "Payment link prepared"),
            ("tokenized_charge", "Tokenized charge mode"),
            ("payment_link_fallback", "Payment link fallback mode"),
            ("pending_real_subscription", "Pending Stripe subscription"),
            ("payment_transaction_reconciled", "Payment transaction reconciled"),
        ],
        string="Event Type",
        required=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("done", "Done"),
            ("warning", "Warning"),
        ],
        string="State",
        default="done",
        required=True,
    )
    account_move_id = fields.Many2one(
        "account.move",
        string="Invoice",
        ondelete="set null",
    )
    payment_transaction_id = fields.Many2one(
        "payment.transaction",
        string="Payment Transaction",
        ondelete="set null",
    )
    description = fields.Text(string="Description")