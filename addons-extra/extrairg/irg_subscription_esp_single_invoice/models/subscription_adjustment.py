from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class IrgSubscriptionAdjustment(models.Model):
    _name = "irg.subscription.adjustment"
    _description = "IRG Subscription Temporary Adjustment"
    _order = "create_date desc, id desc"

    name = fields.Char(string="Name", required=True, default=lambda self: _("New"))
    sale_order_id = fields.Many2one(
        "sale.order",
        string="Subscription",
        required=True,
        ondelete="cascade",
    )
    percentage = fields.Float(string="Reduction Percentage", required=True)
    installment_count = fields.Integer(string="Installments", required=True, default=1)
    effective_date = fields.Date(
        string="Effective Date",
        required=True,
        default=fields.Date.context_today,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("applied", "Applied"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
        required=True,
    )
    note = fields.Text(string="Reason")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="sale_order_id.currency_id",
        store=True,
    )
    line_ids = fields.One2many(
        "irg.subscription.adjustment.line",
        "adjustment_id",
        string="Adjusted Installments",
    )
    applied_line_count = fields.Integer(
        string="Adjusted Installments Count",
        compute="_compute_applied_line_count",
    )

    @api.depends("line_ids")
    def _compute_applied_line_count(self):
        for adjustment in self:
            adjustment.applied_line_count = len(adjustment.line_ids)

    @api.constrains("percentage", "installment_count")
    def _check_adjustment_values(self):
        for adjustment in self:
            if adjustment.percentage <= 0 or adjustment.percentage >= 100:
                raise ValidationError(
                    _("The temporary adjustment percentage must be greater than 0 and lower than 100.")
                )
            if adjustment.installment_count <= 0:
                raise ValidationError(
                    _("The number of installments to adjust must be greater than 0.")
                )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records.filtered(lambda rec: rec.name == _("New")):
            record.name = _("%s - %s%% x %s") % (
                record.sale_order_id.name,
                record.percentage,
                record.installment_count,
            )
        return records


class IrgSubscriptionAdjustmentLine(models.Model):
    _name = "irg.subscription.adjustment.line"
    _description = "IRG Subscription Temporary Adjustment Line"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    adjustment_id = fields.Many2one(
        "irg.subscription.adjustment",
        string="Adjustment",
        required=True,
        ondelete="cascade",
    )
    schedule_id = fields.Many2one(
        "sale.subscription.schedule",
        string="Installment",
        required=True,
        ondelete="restrict",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="schedule_id.currency_id",
        store=True,
    )
    original_amount = fields.Monetary(
        string="Original Amount",
        required=True,
        currency_field="currency_id",
    )
    adjusted_amount = fields.Monetary(
        string="Adjusted Amount",
        required=True,
        currency_field="currency_id",
    )