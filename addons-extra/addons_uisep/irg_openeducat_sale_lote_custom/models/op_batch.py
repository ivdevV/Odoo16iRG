# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class OpBatch(models.Model):
    _inherit = 'op.batch'

    def _check_is_online(self, modality_id, code, name):
        modality = self.env['op.modality'].browse(modality_id) if modality_id else self.env['op.modality']
        if modality:
            return 'online' in (modality.name or '').lower()
        
        code_up = (code or '').upper()
        name_up = (name or '').upper()
        return ('ONL' in code_up or 'ONL' in name_up) and not (
            'HC' in code_up or 'HC' in name_up or
            'PRS' in code_up or 'PRS' in name_up
        )

    @api.onchange('start_date', 'code', 'name', 'modality_id')
    def _onchange_start_date_for_class(self):
        # Solo autocompletar para lotes de modalidad Online (ONL)
        is_onl = self._check_is_online(self.modality_id.id, self.code, self.name)
        if is_onl and self.start_date and not self.date_start_class:
            self.date_start_class = self.start_date
            _logger.info("IRG Custom: Onchange set date_start_class to %s for ONL batch", self.start_date)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            is_onl = self._check_is_online(vals.get('modality_id'), vals.get('code'), vals.get('name'))
            if is_onl and vals.get('start_date') and not vals.get('date_start_class'):
                vals['date_start_class'] = vals['start_date']
                _logger.info("IRG Custom: Create set date_start_class to %s for ONL batch", vals['start_date'])
        return super(OpBatch, self).create(vals_list)

    def write(self, vals):
        res = super(OpBatch, self).write(vals)
        if 'start_date' in vals or 'date_start_class' in vals or 'code' in vals or 'name' in vals or 'modality_id' in vals:
            for record in self:
                is_onl = record._check_is_online(record.modality_id.id, record.code, record.name)
                if is_onl and record.start_date and not record.date_start_class:
                    super(OpBatch, record).write({'date_start_class': record.start_date})
                    _logger.info("IRG Custom: Write set date_start_class to %s for ONL batch %s", record.start_date, record.name)
        return res
