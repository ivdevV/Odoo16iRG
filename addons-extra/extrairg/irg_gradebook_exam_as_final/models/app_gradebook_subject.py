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
            elif rec.gradebook_result_ids:
                final_note = sum(rec.gradebook_result_ids.mapped('scoring_total')) / len(rec.gradebook_result_ids)
            elif rec.final_subject_note:
                final_note = rec.final_subject_note
            elif any([rec.point_average_assignment, rec.point_average_exam, rec.point_average_interaction, rec.point_average_foro]):
                valid_averages = [v for v in [rec.point_average_assignment, rec.point_average_exam, rec.point_average_interaction, rec.point_average_foro] if v > 0]
                final_note = sum(valid_averages) / len(valid_averages) if valid_averages else 0.0
            else:
                final_note = 0.0

            gradebook_id = rec.gradebook_id or rec.gradebook_student_id.gradebook_id
            if gradebook_id and gradebook_id.round_subject_final:
                final_note = rec.round_custom(final_note)

            rec.final_subject_note = final_note
