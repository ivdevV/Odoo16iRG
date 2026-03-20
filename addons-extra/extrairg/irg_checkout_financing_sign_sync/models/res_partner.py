# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Make the website_sale computed field searchable to avoid expensive
    # fallback errors during sale.order write trigger propagation.
    last_website_so_id = fields.Many2one(
        'sale.order',
        compute='_compute_last_website_so_id',
        search='_search_last_website_so_id',
        string='Last Online Sales Order',
    )

    def _search_last_website_so_id(self, operator, value):
        SaleOrder = self.env['sale.order'].sudo()

        negative = operator in ('!=', '<>', 'not in')
        op = operator
        val = value

        if operator in ('!=', '<>'):
            op = '='
        elif operator == 'not in':
            op = 'in'

        if op == 'in':
            val = list(value) if isinstance(value, (list, tuple, set)) else [value]

        if op in ('=', 'in'):
            order_domain = [('id', op, val)]
            partner_ids = SaleOrder.search(order_domain).mapped('partner_id.commercial_partner_id').ids
            if negative:
                return [('id', 'not in', partner_ids or [0])]
            return [('id', 'in', partner_ids or [0])]

        # Fallback: return a harmless domain for unsupported operators.
        return [('id', 'in', [0])]

    @api.constrains('vat', 'country_id')
    def check_vat(self):
        # IRG: This instance does not perform EU VIES network validation.
        # Skipping unconditionally prevents external TCP timeouts (3+ minutes)
        # that block checkout and any other partner write operation.
        # context flags are irrelevant — the network call is never needed here.
        _logger.debug("IRG check_vat: VIES validation unconditionally skipped for %s", self.mapped('name'))
        return
