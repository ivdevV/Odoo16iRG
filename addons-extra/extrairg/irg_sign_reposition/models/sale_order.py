# -*- coding: utf-8 -*-

from odoo import models


class SaleOrderSignReposition(models.Model):
    _inherit = 'sale.order'

    def action_send_to_sign(self):
        result = super().action_send_to_sign()

        target_pos_y_by_page = {
            1: 0.800,
            3: 0.450,
        }

        for order in self:
            if not order.sign_id:
                continue

            sign_items = self.env['sign.item'].search([
                ('template_id', '=', order.sign_id.id),
                ('type_id', '=', 1),
            ])
            for item in sign_items:
                target_pos_y = target_pos_y_by_page.get(item.page)
                if target_pos_y is None:
                    continue
                item.write({'posY': target_pos_y})

        return result
