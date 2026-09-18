# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import models

IRG_HOMECLASS_SUBJECT_LEAD_DAYS = 3


class OpBatch(models.Model):
    _inherit = 'op.batch'

    def _irg_apply_homeclass_subject_lead_days(self):
        self.ensure_one()
        lead = timedelta(days=IRG_HOMECLASS_SUBJECT_LEAD_DAYS)
        self_ctx = self.with_context(skip_homeclass_sync=True)
        for line in self_ctx.subject_to_batch_ids:
            if not line.date_from:
                continue
            new_date = line.date_from - lead
            if new_date != line.date_from:
                line.write({'date_from': new_date})
        return True

    def _sync_homeclass_calendar(self):
        result = super()._sync_homeclass_calendar()
        if result:
            self._irg_apply_homeclass_subject_lead_days()
        return result
