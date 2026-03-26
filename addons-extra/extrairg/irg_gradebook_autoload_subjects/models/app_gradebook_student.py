# -*- coding: utf-8 -*-
from odoo import models, api


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    @api.onchange('admission_id')
    def _onchange_admission_autoload_subjects(self):
        """
        Populates gradebook_subject_ids in the UI as soon as the user
        selects an admission, before saving.
        """
        if not self.admission_id or not self.admission_id.course_id:
            return
        course = self.admission_id.course_id
        existing_subject_ids = self.gradebook_subject_ids.mapped('op_subject_id').ids
        subjects_to_add = course.subject_ids.filtered(
            lambda s: s.subject_type == 'compulsory'
            and s.id not in existing_subject_ids
        )
        GradebookSubject = self.env['app.gradebook.subject']
        for s in subjects_to_add:
            self.gradebook_subject_ids += GradebookSubject.new({
                'op_subject_id': s.id,
            })
