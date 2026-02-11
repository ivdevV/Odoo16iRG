# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    irg_force_price_unit = fields.Float(
        string="IRG Forced Price",
        help="If set, this unit price is enforced to avoid pricelist recompute overrides.",
        copy=False,
    )

    def _compute_price_unit(self):
        super()._compute_price_unit()
        for line in self:
            if line.irg_force_price_unit and line.irg_force_price_unit > 0:
                line.price_unit = line.irg_force_price_unit
