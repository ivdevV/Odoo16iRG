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
            if (
                order.irg_payment_link_fallback_enabled
                and order.irg_subscription_stripe_mode in ("payment_link_fallback", "tokenized_charge")
                and "link_payment_static" in move._fields
                and hasattr(move, "compute_link_payment_link")
            ):
                move.compute_link_payment_link()
                if move.link_payment:
                    move.link_payment_static = move.link_payment
                    order._irg_log_bridge_event(
                        event_type="payment_link_prepared",
                        account_move=move,
                        description="Fallback payment link prepared on the single invoice.",
                    )
            order.sudo()._irg_register_single_invoice(move)
        return result