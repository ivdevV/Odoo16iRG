# -*- coding: utf-8 -*-
import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.constrains('vat', 'country_id')
    def check_vat(self):
        # IRG: This instance does not perform EU VIES network validation.
        # Skipping unconditionally prevents external TCP timeouts (3+ minutes)
        # that block checkout and any other partner write operation.
        # context flags are irrelevant — the network call is never needed here.
        _logger.debug("IRG check_vat: VIES validation unconditionally skipped for %s", self.mapped('name'))
        return
