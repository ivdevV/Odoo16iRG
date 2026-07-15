# -*- coding: utf-8 -*-
from odoo import api, models


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    @api.depends(
        'gradebook_id.final_calculation_mode',
        'course_id.name',
        'course_id.code',
        'course_id.course_type_id.name',
        'course_id.course_type_id.code',
        'course_id.product_template_id.categ_id.name',
        'course_id.product_template_id.categ_id.code',
        'gradebook_subject_ids.final_subject_note',
        'gradebook_subject_ids.op_subject_id.name',
        'gradebook_subject_ids.op_subject_id.code',
        'gradebook_subject_ids.op_subject_id.subject_type',
    )
    def _compute_diploma_recovery_required(self):
        return super()._compute_diploma_recovery_required()

    @api.depends(
        'gradebook_id.final_calculation_mode',
        'course_id.name',
        'course_id.code',
        'course_id.course_type_id.name',
        'course_id.course_type_id.code',
        'course_id.product_template_id.categ_id.name',
        'course_id.product_template_id.categ_id.code',
        'gradebook_subject_ids.final_subject_note',
        'gradebook_subject_ids.op_subject_id.name',
        'gradebook_subject_ids.op_subject_id.code',
        'gradebook_subject_ids.op_subject_id.subject_type',
        'diploma_recovery_required',
        'diploma_recovery_score',
        'diploma_recovery_applied',
    )
    def _amount_prod_final(self):
        """Keep NLEX's inherited average, then restore special weighting."""
        super()._amount_prod_final()
        for gradebook in self:
            diploma_final = gradebook._get_diploma_final_score()
            if diploma_final is not False:
                gradebook.total_final = diploma_final

    @api.depends(
        'student_id',
        'gradebook_id.final_calculation_mode',
        'course_id.name',
        'course_id.code',
        'course_id.course_type_id.name',
        'course_id.course_type_id.code',
        'course_id.product_template_id.categ_id.name',
        'course_id.product_template_id.categ_id.code',
        'gradebook_subject_ids',
        'gradebook_subject_ids.final_subject_note',
        'gradebook_subject_ids.op_subject_id',
        'gradebook_subject_ids.op_subject_id.name',
        'gradebook_subject_ids.op_subject_id.code',
        'gradebook_subject_ids.op_subject_id.subject_type',
        'diploma_recovery_required',
        'diploma_recovery_score',
        'diploma_recovery_applied',
    )
    def compute_avg_score(self):
        """Keep NLEX's inherited average, then restore special weighting."""
        super().compute_avg_score()
        for gradebook in self:
            diploma_final = gradebook._get_diploma_final_score()
            if diploma_final is not False:
                gradebook.avg_score = diploma_final

    def _get_diploma_weighting_values(self):
        """Return the 50/50 inputs after removing all NLEX/EX subjects."""
        self.ensure_one()
        if not self.gradebook_id:
            return False
        if self.gradebook_id.final_calculation_mode != 'diploma_50_50':
            return False
        if not self._is_diplomado_course():
            return False

        compulsory_subjects = self.gradebook_subject_ids.filtered(
            lambda line: (
                line.op_subject_id.subject_type == 'compulsory'
                and not line.op_subject_id.irg_is_grade_exempt()
            )
        )
        presencial_subjects = compulsory_subjects.filtered(
            lambda line: self._is_presential_module_subject(line)
        )
        if len(presencial_subjects) != 1:
            return False

        non_presential_subjects = compulsory_subjects - presencial_subjects
        if not non_presential_subjects:
            return False

        presencial_score = presencial_subjects.final_subject_note
        non_presential_average = (
            sum(non_presential_subjects.mapped('final_subject_note'))
            / len(non_presential_subjects)
        )
        return {
            'base_final': (
                presencial_score * 0.5
                + non_presential_average * 0.5
            ),
            'presencial_score': presencial_score,
            'non_presential_average': non_presential_average,
            'non_presential_count': len(non_presential_subjects),
            'non_presential_weight': 50.0 / len(non_presential_subjects),
        }
