# -*- coding: utf-8 -*-
from odoo import api, fields, models


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    irg_class_start_date = fields.Date(
        string='Fecha de inicio de clases',
        copy=False,
    )

    @api.onchange('batch_id')
    def _onchange_batch_id_set_due_date_from_batch(self):
        if self.batch_id and self.batch_id.end_date:
            self.due_date = self.batch_id.end_date

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if vals.get('batch_id') and 'due_date' not in vals and record.batch_id and record.batch_id.end_date:
            record.due_date = record.batch_id.end_date
        return record

    def write(self, vals):
        res = super().write(vals)
        if 'batch_id' in vals and 'due_date' not in vals:
            for record in self.filtered(lambda r: r.batch_id and r.batch_id.end_date):
                record.due_date = record.batch_id.end_date
        return res
