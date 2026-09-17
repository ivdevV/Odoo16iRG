# -*- coding: utf-8 -*-
from datetime import date

from odoo import api, fields, models


class IrgDiplomadoRegistry(models.Model):
    _inherit = 'irg.diplomado.registry'

    @api.model
    def _irg_fixed_issue_date(self):
        today = fields.Date.context_today(self)
        return date(today.year, 9, 26)

    def _default_issue_date(self):
        return self._irg_fixed_issue_date()

    issue_date = fields.Date(default=_default_issue_date)
