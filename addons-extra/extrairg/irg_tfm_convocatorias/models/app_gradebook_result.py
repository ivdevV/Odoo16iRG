from odoo import api, models


_TFM_PROGRESS_FIELDS = frozenset({
    'gradebook_subject_id',
    'scoring_total',
    'survey_type',
})
_TFM_DEFER_GRADE_TRIGGER = 'irg_tfm_defer_grade_trigger'


class AppGradebookResult(models.Model):
    _inherit = 'app.gradebook.result'

    def _irg_tfm_affected_subjects(self):
        return self.mapped('gradebook_subject_id').exists()

    def _irg_tfm_refresh_affected_enrollments(self, subjects):
        """Recompute progress and activate only enrollments derived from grades."""
        subjects = subjects.sudo().exists()
        pairs = {
            (
                subject.gradebook_student_id.student_id.id,
                subject.gradebook_student_id.course_id.id,
            )
            for subject in subjects
            if subject.gradebook_student_id.student_id
            and subject.gradebook_student_id.course_id
        }
        if not pairs:
            return

        student_ids = list({student_id for student_id, _course_id in pairs})
        course_ids = list({course_id for _student_id, course_id in pairs})
        enrollments = self.env['op.student.course'].sudo().search([
            ('student_id', 'in', student_ids),
            ('course_id', 'in', course_ids),
            ('course_id.activate_tesis', '=', True),
        ])
        enrollments = enrollments.filtered(
            lambda enrollment: (
                enrollment.student_id.id,
                enrollment.course_id.id,
            ) in pairs
        )
        if not enrollments:
            return

        self.env.cr.execute(
            'SELECT id FROM op_student_course '
            'WHERE id IN %s ORDER BY id FOR UPDATE',
            [tuple(enrollments.ids)],
        )
        subjects.compute_final_subject_note()
        subjects.flush_recordset(['final_subject_note'])
        enrollments.invalidate_recordset(['completion_porc'])
        for enrollment in enrollments:
            enrollment._irg_ensure_tfm_record()

    @api.model
    def create(self, values):
        already_deferred = self.env.context.get(_TFM_DEFER_GRADE_TRIGGER)
        records = super(
            AppGradebookResult,
            self.with_context(**{_TFM_DEFER_GRADE_TRIGGER: True}),
        ).create(values)
        if not already_deferred:
            records.with_context(
                **{_TFM_DEFER_GRADE_TRIGGER: False}
            )._irg_tfm_refresh_affected_enrollments(
                records._irg_tfm_affected_subjects()
            )
        return records

    def write(self, values):
        should_refresh = (
            not self.env.context.get(_TFM_DEFER_GRADE_TRIGGER)
            and bool(_TFM_PROGRESS_FIELDS.intersection(values))
        )
        previous_subjects = self._irg_tfm_affected_subjects() if should_refresh else self.browse()
        result = super().write(values)
        if should_refresh:
            subjects = previous_subjects | self._irg_tfm_affected_subjects()
            self._irg_tfm_refresh_affected_enrollments(subjects)
        return result

    def unlink(self):
        should_refresh = not self.env.context.get(_TFM_DEFER_GRADE_TRIGGER)
        subjects = self._irg_tfm_affected_subjects() if should_refresh else self.browse()
        result = super().unlink()
        if should_refresh:
            self._irg_tfm_refresh_affected_enrollments(subjects)
        return result
