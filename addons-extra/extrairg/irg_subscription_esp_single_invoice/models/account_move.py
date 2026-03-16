from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    irg_single_subscription_invoice = fields.Boolean(
        string="IRG Single Subscription Invoice",
        default=False,
        copy=False,
        index=True,
    )

    def action_post(self):
        result = super().action_post()
        for move in self.filtered(lambda invoice: invoice.move_type == "out_invoice"):
            order = move.order_subscription_id or move.line_ids.sale_line_ids.order_id[:1]
            if not order or not order._irg_should_use_single_invoice_strategy():
                continue

            move.sudo().write(
                {
                    "irg_single_subscription_invoice": True,
                    "order_subscription_id": order.id,
                }
            )
            order.sudo()._irg_register_single_invoice(move)
        return result