# -*- coding: utf-8 -*-
import datetime
from odoo import models


class OpCourse(models.Model):
    _inherit = 'op.course'

    def get_subjects_visible_for_batch(self, batch, admission=None):
        self.ensure_one()
        if admission:
            if admission.irg_has_online_subject_opening_context():
                online_subjects = admission.irg_get_visible_online_subjects_for_date(datetime.date.today())
                return online_subjects.filtered(lambda s: s.is_visible_for_batch(batch))

        return super(OpCourse, self).get_subjects_visible_for_batch(batch, admission)
