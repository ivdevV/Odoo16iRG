# -*- coding: utf-8 -*-
from odoo import models, fields


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    irg_force_price_unit = fields.Float(
        string="IRG Forced Price",
        help="If set, this unit price is enforced to avoid pricelist recompute overrides.",
        copy=False,
    )
    irg_force_price_unit_set = fields.Boolean(
        string="IRG Forced Price Set",
        help="Marks that the forced price should be applied even when the value is 0.",
        copy=False,
    )
    irg_line_type = fields.Selection(
        [
            ("master", "Master"),
            ("financing", "Financing"),
            ("matricula", "Matricula"),
            ("matricula_discount", "Matricula Discount"),
        ],
        string="IRG Line Type",
        copy=False,
    )
    irg_parent_line_id = fields.Many2one(
        "sale.order.line",
        string="IRG Parent Line",
        copy=False,
    )

    def _compute_price_unit(self):
        super()._compute_price_unit()
        for line in self:
            if line.irg_force_price_unit_set or (line.irg_force_price_unit and line.irg_force_price_unit > 0):
                line.price_unit = line.irg_force_price_unit
