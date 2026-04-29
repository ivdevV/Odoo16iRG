# -*- coding: utf-8 -*-
from odoo import models, api


class AppGradebookSubject(models.Model):
    _inherit = 'app.gradebook.subject'

    @api.depends(
        'gradebook_result_ids.scoring_total',
        'gradebook_result_ids.survey_type',
        'gradebook_id.round_subject_final',
        'gradebook_student_id.gradebook_id.round_subject_final',
    )
    def compute_final_subject_note(self):
        """
        La nota final de la asignatura es la nota del examen registrado.

        - Si hay un único examen, se toma su nota directamente.
        - Si hay varios exámenes (fallback), se calcula el promedio aritmético.
        - Si no hay exámenes, la nota final es 0.0.
        - El redondeo respeta la configuración round_subject_final de la plantilla.

        Las categorías assignment, interaction y foro NO influyen en este cálculo.
        """
        for rec in self:
            exam_results = rec.gradebook_result_ids.filtered(
                lambda r: r.survey_type == 'exam'
            )
            if exam_results:
                final_note = sum(exam_results.mapped('scoring_total')) / len(exam_results)
            else:
                final_note = 0.0

            gradebook_id = rec.gradebook_id or rec.gradebook_student_id.gradebook_id
            if gradebook_id and gradebook_id.round_subject_final:
                final_note = rec.round_custom(final_note)

            rec.final_subject_note = final_note

    @api.depends(
        'gradebook_id',
        'gradebook_id.gradebook_template_ids',
        'gradebook_student_id.gradebook_id',
        'gradebook_student_id.gradebook_id.gradebook_template_ids',
    )
    def compute_data_show(self):
        """Override: assignments do not participate in the final grade under
        irg_gradebook_exam_as_final, so we always hide the assignment block
        and remove the assignment-count requirement from the template check.
        """
        super().compute_data_show()
        for rec in self:
            rec.show_assignment = False

    @api.depends('op_subject_id', 'admission_id')
    def compute_gradebook_id(self):
        """Override: always assign the 'Solo Examen' template regardless of
        what is configured on the op.subject record.
        This ensures no assignment lines are required anywhere in the flow.
        """
        solo_examen = self.env.ref(
            'irg_gradebook_exam_as_final.gradebook_template_solo_examen',
            raise_if_not_found=False,
        )
        for rec in self:
            rec.gradebook_id = solo_examen if solo_examen else False
