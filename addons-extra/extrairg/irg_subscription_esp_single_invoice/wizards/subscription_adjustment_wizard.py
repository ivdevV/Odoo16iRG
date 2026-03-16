from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError


class IrgSubscriptionAdjustmentWizard(models.TransientModel):
    _name = "irg.subscription.adjustment.wizard"
    _description = "IRG Subscription Temporary Adjustment Wizard"

    sale_order_id = fields.Many2one(
        "sale.order",
        string="Subscription",
        required=True,
    )
    percentage = fields.Float(string="Reduction Percentage", required=True, default=20.0)
    installment_count = fields.Integer(string="Installments", required=True, default=6)
    effective_date = fields.Date(
        string="Effective Date",
        required=True,
        default=fields.Date.context_today,
    )
    note = fields.Text(string="Reason")

    def action_apply(self):
        self.ensure_one()

        if self.percentage <= 0 or self.percentage >= 100:
            raise ValidationError(
                _("The temporary adjustment percentage must be greater than 0 and lower than 100.")
            )
        if self.installment_count <= 0:
            raise ValidationError(
                _("The number of installments to adjust must be greater than 0.")
            )

        order = self.sale_order_id
        if not order._irg_should_use_single_invoice_strategy():
            raise UserError(
                _("The temporary adjustment wizard is only available for the single invoice subscription strategy.")
            )

        target_lines = order.subscription_schedule.filtered(
            lambda line: line.date_due
            and line.date_due >= self.effective_date
            and line.payment_state == "not_paid"
        ).sorted("date_due")

        target_lines = target_lines[: self.installment_count]
        if not target_lines:
            raise UserError(
                _("There are no future unpaid installments available for the selected effective date.")
            )
        if len(target_lines) < self.installment_count:
            raise UserError(
                _("Only %s future unpaid installments are available for adjustment.")
                % len(target_lines)
            )

        adjustment = self.env["irg.subscription.adjustment"].create(
            {
                "sale_order_id": order.id,
                "percentage": self.percentage,
                "installment_count": self.installment_count,
                "effective_date": self.effective_date,
                "note": self.note,
            }
        )

        for sequence, line in enumerate(target_lines, start=1):
            original_amount = (
                line.irg_original_amount_recurring_taxinc or line.amount_recurring_taxinc
            )
            adjusted_amount = line.currency_id.round(
                original_amount * (1.0 - (self.percentage / 100.0))
            )
            if adjusted_amount < 0:
                raise UserError(_("The adjusted amount cannot be negative."))

            line.write(
                {
                    "amount_recurring_taxinc": adjusted_amount,
                    "irg_original_amount_recurring_taxinc": original_amount,
                    "irg_last_adjustment_id": adjustment.id,
                }
            )
            self.env["irg.subscription.adjustment.line"].create(
                {
                    "sequence": sequence * 10,
                    "adjustment_id": adjustment.id,
                    "schedule_id": line.id,
                    "original_amount": original_amount,
                    "adjusted_amount": adjusted_amount,
                }
            )

        adjustment.state = "applied"

        return {
            "name": _("Temporary Installment Adjustment"),
            "type": "ir.actions.act_window",
            "res_model": "irg.subscription.adjustment",
            "res_id": adjustment.id,
            "view_mode": "form",
            "target": "current",
        }