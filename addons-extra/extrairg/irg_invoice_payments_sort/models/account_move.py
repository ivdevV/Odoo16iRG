from datetime import date as dt_date

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _compute_payments_widget_reconciled_info(self):
        res = super()._compute_payments_widget_reconciled_info()
        for move in self:
            widget = move.invoice_payments_widget
            if not widget or not isinstance(widget, dict):
                continue
            content = widget.get("content")
            if not content or len(content) < 2:
                continue
            widget["content"] = sorted(
                content,
                key=lambda p: (p.get("date") or dt_date.min, p.get("amount", 0)),
            )
            move.invoice_payments_widget = widget
        return res
