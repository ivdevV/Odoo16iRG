# -*- coding: utf-8 -*-
from odoo import api, fields, models


class IrgDiplomadoWizard(models.TransientModel):
    _inherit = 'irg.diplomado.wizard'

    def _default_issue_date(self):
        return self.env['irg.diplomado.registry']._irg_fixed_issue_date()

    issue_date = fields.Date(
        default=_default_issue_date,
        readonly=True,
    )

    @api.model
    def create(self, vals):
        vals = dict(vals)
        vals['issue_date'] = self.env['irg.diplomado.registry']._irg_fixed_issue_date()
        return super().create(vals)

    def write(self, vals):
        vals = dict(vals)
        vals['issue_date'] = self.env['irg.diplomado.registry']._irg_fixed_issue_date()
        return super().write(vals)
