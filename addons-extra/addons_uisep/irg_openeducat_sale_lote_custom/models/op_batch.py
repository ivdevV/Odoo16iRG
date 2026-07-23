# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class OpBatch(models.Model):
    _inherit = 'op.batch'

    irg_is_intensive = fields.Boolean(
        string='Es Intensivo',
        compute='_compute_irg_is_intensive',
        store=True,
        help='Indica si el grupo/lote pertenece a la modalidad Cursos Intensivos.',
    )

    @api.depends('code', 'name', 'modality_id', 'modality_id.code', 'modality_id.name')
    def _compute_irg_is_intensive(self):
        for record in self:
            is_int = False
            if record.modality_id:
                mod_code = (record.modality_id.code or '').upper()
                mod_name = (record.modality_id.name or '').lower()
                if mod_code == 'IN' or 'intensiv' in mod_name:
                    is_int = True
            if not is_int:
                code_up = (record.code or '').upper()
                name_up = (record.name or '').upper()
                if 'IN' in code_up or 'INTENSIV' in name_up:
                    if not ('ONLINE' in name_up and 'INTENSIV' not in name_up):
                        is_int = True
            record.irg_is_intensive = is_int

    def _check_is_online(self, modality_id, code, name):
        modality = self.env['op.modality'].browse(modality_id) if modality_id else self.env['op.modality']
        if modality:
            mod_name = (modality.name or '').lower()
            mod_code = (modality.code or '').upper()
            if 'online' in mod_name or mod_code == 'IN' or 'intensiv' in mod_name:
                return True
        
        code_up = (code or '').upper()
        name_up = (name or '').upper()
        if ('ONL' in code_up or 'ONL' in name_up or 'IN' in code_up or 'INTENSIV' in name_up):
            if not ('HC' in code_up or 'HC' in name_up or 'PRS' in code_up or 'PRS' in name_up):
                return True
        return False

    @api.onchange('start_date', 'code', 'name', 'modality_id')
    def _onchange_start_date_for_class(self):
        # Autocompletar fecha de clases para Online e Intensivos
        is_onl = self._check_is_online(self.modality_id.id, self.code, self.name)
        if is_onl and self.start_date and not self.date_start_class:
            self.date_start_class = self.start_date
            _logger.info("IRG Custom: Onchange set date_start_class to %s for batch", self.start_date)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            is_onl = self._check_is_online(vals.get('modality_id'), vals.get('code'), vals.get('name'))
            if is_onl and vals.get('start_date') and not vals.get('date_start_class'):
                vals['date_start_class'] = vals['start_date']
                _logger.info("IRG Custom: Create set date_start_class to %s for batch", vals['start_date'])
        return super(OpBatch, self).create(vals_list)

    def write(self, vals):
        res = super(OpBatch, self).write(vals)
        if 'start_date' in vals or 'date_start_class' in vals or 'code' in vals or 'name' in vals or 'modality_id' in vals:
            for record in self:
                is_onl = record._check_is_online(record.modality_id.id, record.code, record.name)
                if is_onl and record.start_date and not record.date_start_class:
                    super(OpBatch, record).write({'date_start_class': record.start_date})
                    _logger.info("IRG Custom: Write set date_start_class to %s for batch %s", record.start_date, record.name)
        return res
