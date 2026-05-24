# -*- coding: utf-8 -*-
import datetime
import logging
from odoo import models

_logger = logging.getLogger(__name__)


class OpCourse(models.Model):
    _inherit = 'op.course'

    def get_subjects_visible_for_batch(self, batch, admission=None):
        self.ensure_one()
        _logger.info("[PORTAL_VISIBILITY] get_subjects_visible_for_batch called for course: %s, batch: %s (ID: %s), admission: %s",
                     self.name, batch.name if batch else 'None', batch.id if batch else 'None', admission.id if admission else 'None')
        if admission:
            # Let's log why irg_has_online_subject_opening_context evaluates to True or False
            batch_code = (admission.batch_id.code or '').upper()
            has_onl_token = bool(batch_code and 'ONL' in batch_code and 'MONL' not in batch_code)
            
            has_dates = bool(admission.batch_id.subject_to_batch_ids.filtered(lambda s: s.date_from and s.date_to))
            is_opening_batch = has_onl_token and not has_dates
            
            _logger.info("[PORTAL_VISIBILITY] -> Diagnostics: batch_code='%s', has_onl_token=%s, has_dates_in_batch=%s, is_opening_batch=%s, admission_date=%s, course_id=%s, batch_id=%s",
                         batch_code, has_onl_token, has_dates, is_opening_batch, admission.admission_date, bool(admission.course_id), bool(admission.batch_id))

            has_context = admission.irg_has_online_subject_opening_context()
            _logger.info("[PORTAL_VISIBILITY] -> admission has_online_subject_opening_context: %s", has_context)
            if has_context:
                online_subjects = admission.irg_get_visible_online_subjects_for_date(datetime.date.today())
                res = online_subjects.filtered(lambda s: s.is_visible_for_batch(batch))
                _logger.info("[PORTAL_VISIBILITY] -> online subjects returned: %s", res.mapped('name'))
                return res

        res = super(OpCourse, self).get_subjects_visible_for_batch(batch, admission)
        _logger.info("[PORTAL_VISIBILITY] -> fallback returned: %s", res.mapped('name'))
        return res
