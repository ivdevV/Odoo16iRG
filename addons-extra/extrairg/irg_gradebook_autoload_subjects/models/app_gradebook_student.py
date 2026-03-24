# -*- coding: utf-8 -*-
from odoo import models, api


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    def _autoload_subjects(self):
        """
        Auto-populates gradebook subjects (app.gradebook.subject) from the
        compulsory subjects of the linked course (op.course.subject_ids).
        Only adds subjects not already present — never removes existing ones,
        to avoid losing recorded evaluation results.
        """
        GradebookSubject = self.env['app.gradebook.subject']
        for rec in self:
            if not rec.course_id:
                continue
            existing_subject_ids = rec.gradebook_subject_ids.mapped('op_subject_id').ids
            subjects_to_add = rec.course_id.subject_ids.filtered(
                lambda s: s.subject_type == 'compulsory'
                and s.id not in existing_subject_ids
            )
            if subjects_to_add:
                GradebookSubject.create([
                    {
                        'op_subject_id': s.id,
                        'gradebook_student_id': rec.id,
                    }
                    for s in subjects_to_add
                ])

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._autoload_subjects()
        return records

    def write(self, vals):
        result = super().write(vals)
        # Re-sync subjects when admission changes (course_id is a related of admission_id)
        if 'admission_id' in vals:
            self._autoload_subjects()
        return result
