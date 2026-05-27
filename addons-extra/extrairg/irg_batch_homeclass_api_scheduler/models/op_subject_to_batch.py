# -*- coding: utf-8 -*-
from odoo import models, fields, api

class OpSubjectToBatch(models.Model):
    _inherit = 'op.subject.to.batch'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(OpSubjectToBatch, self).create(vals_list)
        if not self.env.context.get('skip_homeclass_sync'):
            batches_to_sync = records.mapped('batch_id').filtered(lambda b: b.is_homeclass_batch)
            for batch in batches_to_sync:
                batch.with_context(skip_homeclass_sync=True)._sync_homeclass_calendar()
        return records

    def write(self, vals):
        res = super(OpSubjectToBatch, self).write(vals)
        if not self.env.context.get('skip_homeclass_sync'):
            if any(f in vals for f in ['subject_id', 'code']):
                batches_to_sync = self.mapped('batch_id').filtered(lambda b: b.is_homeclass_batch)
                for batch in batches_to_sync:
                    batch.with_context(skip_homeclass_sync=True)._sync_homeclass_calendar()
        return res

    def unlink(self):
        batches_to_sync = self.mapped('batch_id').filtered(lambda b: b.is_homeclass_batch)
        res = super(OpSubjectToBatch, self).unlink()
        if not self.env.context.get('skip_homeclass_sync'):
            for batch in batches_to_sync:
                batch.with_context(skip_homeclass_sync=True)._sync_homeclass_calendar()
        return res
