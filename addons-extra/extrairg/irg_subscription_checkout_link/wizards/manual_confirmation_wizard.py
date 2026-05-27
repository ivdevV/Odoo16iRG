# -*- coding: utf-8 -*-

from odoo import models


class ManualConfirmationWizard(models.TransientModel):
    _inherit = "irg.manual.confirmation.wizard"

    def action_confirm(self):
        self.ensure_one()
        order = self.order_id
        res = super().action_confirm()
        if order:
            order.sudo()._irg_consume_pending_subscription_checkout()
        return res
