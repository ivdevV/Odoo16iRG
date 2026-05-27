# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class OpBatch(models.Model):
    _inherit = 'op.batch'

    @api.onchange('start_date', 'code', 'name')
    def _onchange_start_date_for_class(self):
        # Solo autocompletar para lotes de modalidad Online (ONL)
        is_onl = 'ONL' in (self.code or '').upper() or 'ONL' in (self.name or '').upper()
        if is_onl and self.start_date and not self.date_start_class:
            self.date_start_class = self.start_date
            _logger.info("IRG Custom: Onchange set date_start_class to %s for ONL batch", self.start_date)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            code = vals.get('code') or ''
            name = vals.get('name') or ''
            is_onl = 'ONL' in code.upper() or 'ONL' in name.upper()
            if is_onl and vals.get('start_date') and not vals.get('date_start_class'):
                vals['date_start_class'] = vals['start_date']
                _logger.info("IRG Custom: Create set date_start_class to %s for ONL batch", vals['start_date'])
        return super(OpBatch, self).create(vals_list)

    def write(self, vals):
        res = super(OpBatch, self).write(vals)
        if 'start_date' in vals or 'date_start_class' in vals or 'code' in vals or 'name' in vals:
            for record in self:
                is_onl = 'ONL' in (record.code or '').upper() or 'ONL' in (record.name or '').upper()
                if is_onl and record.start_date and not record.date_start_class:
                    super(OpBatch, record).write({'date_start_class': record.start_date})
                    _logger.info("IRG Custom: Write set date_start_class to %s for ONL batch %s", record.start_date, record.name)
        return res
