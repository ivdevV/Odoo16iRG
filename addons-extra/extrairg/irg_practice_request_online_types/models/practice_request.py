# -*- coding: utf-8 -*-

from odoo import _, api, models
from odoo.exceptions import ValidationError

from .online_batch import IRG_ONLINE_MASTER_PRACTICE_TYPES


class PracticeRequest(models.Model):
    _inherit = 'practice.request'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._irg_check_portal_online_practice_type()
        return records

    def write(self, vals):
        res = super().write(vals)
        if any(key in vals for key in ('practice_center_type_id', 'course_id')):
            self._irg_check_portal_online_practice_type()
        return res

    def _irg_check_portal_online_practice_type(self):
        if not self.env.user.has_group('base.group_portal'):
            return
        for record in self:
            if not record._irg_online_practice_type_is_allowed():
                raise ValidationError(
                    _('Para másteres online solo puedes elegir convalidación '
                      'por experiencia, convalidación por TFM o prácticas '
                      'asíncronas.')
                )

    def _irg_online_practice_type_is_allowed(self):
        self.ensure_one()
        enrollment = self.course_id
        if not enrollment or not enrollment.irg_is_online_master_batch:
            return True
        practice_type = self.practice_center_type_id
        if not practice_type:
            return True
        return practice_type.type_of_practice in IRG_ONLINE_MASTER_PRACTICE_TYPES
