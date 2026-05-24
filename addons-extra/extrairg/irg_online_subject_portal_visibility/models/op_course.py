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
