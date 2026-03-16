from odoo import fields, models


class SaleSubscriptionSchedule(models.Model):
    _inherit = "sale.subscription.schedule"

    irg_original_amount_recurring_taxinc = fields.Monetary(
        string="IRG Original Installment Amount",
        copy=False,
        currency_field="currency_id",
        help="Stores the original installment amount before any temporary IRG adjustment is applied.",
    )
    irg_last_adjustment_id = fields.Many2one(
        "irg.subscription.adjustment",
        string="IRG Last Adjustment",
        copy=False,
    )