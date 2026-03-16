from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _reconcile_after_done(self):
        single_invoice_orders = self.mapped("sale_order_ids").filtered(
            lambda order: order._irg_should_use_single_invoice_strategy()
        )
        draft_orders = single_invoice_orders.filtered(lambda order: order.state in ("draft", "sent"))
        if draft_orders:
            draft_orders.sudo().action_confirm()

        result = super()._reconcile_after_done()

        if single_invoice_orders:
            single_invoice_orders.sudo()._irg_ensure_single_invoice()

        return result