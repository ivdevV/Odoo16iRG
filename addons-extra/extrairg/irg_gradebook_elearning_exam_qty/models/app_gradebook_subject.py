# -*- coding: utf-8 -*-
from odoo import models


class AppGradebookSubject(models.Model):
    _inherit = 'app.gradebook.subject'

    def _irg_slide_allows_gradebook_batch(self, slide, batch):
        self.ensure_one()
        allowed = slide.sudo().allowed_batch_ids
        if not allowed:
            return True
        return bool(batch) and batch in allowed

    def _irg_elearning_exam_qty(self):
        self.ensure_one()
        channel = self.op_subject_id.slide_channel_id
        if not channel:
            return 0
        batch = self.gradebook_student_id.batch_id
        survey_ids = set()
        for slide in channel.slide_ids.sudo():
            if slide.is_category or not slide.is_published:
                continue
            survey = slide.survey_id
            if not survey or survey.survey_type != 'exam':
                continue
            if not self._irg_slide_allows_gradebook_batch(slide, batch):
                continue
            survey_ids.add(survey.id)
        return len(survey_ids)

    def _get_gradebook_info(self, rec):
        info = super()._get_gradebook_info(rec)
        if rec.gradebook_student_id.state == 'done':
            return info
        qty = rec._irg_elearning_exam_qty()
        if qty:
            info['exam']['qty'] = qty
        return info
