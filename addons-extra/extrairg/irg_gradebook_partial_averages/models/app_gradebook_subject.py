# -*- coding: utf-8 -*-
from odoo import models, api


class AppGradebookSubject(models.Model):
    _inherit = 'app.gradebook.subject'

    @api.depends('gradebook_result_ids.scoring_total', 'gradebook_id', 'gradebook_student_id.gradebook_id')
    def compute_point_average(self):
        """
        Recalcula los promedios de la asignatura por tipo de resultado.

        Sobrescribe el método original de isep_gradebook para que los
        promedios de "assignment" y "exam" se calculen con la media
        aritmética de los resultados realmente registrados, aunque su
        cantidad no coincida con la "qty" configurada en la línea de la
        plantilla de calificaciones (gradebook_id).

        Antes, si el nº de resultados no era exactamente igual a la qty de
        la plantilla, el promedio se forzaba a 0 y ese 0 quedaba persistido
        (campos store) al aplicar o cambiar de plantilla, aunque hubiera
        resultados reales registrados.

        Reglas:
        - Con >= 1 resultado del tipo: promedio aritmético de los
          resultados existentes (parcial, sin exigir que coincida con qty).
        - Con 0 resultados: 0 (comportamiento original, correcto).
        - "interaction" y "foro" mantienen la lógica original (exigen
          exactamente 1 resultado; hay constraint que impide más de 1).

        El resto del método (guard de plantilla, construcción de info_*,
        redondeo con round_subject_avg) se preserva sin cambios respecto al
        original.
        """
        for rec in self:
            assignment_total = 0
            assignment_count = 0

            exam_total = 0
            exam_count = 0

            interaction_total = 0
            interaction_count = 0

            foro_total = 0
            foro_count = 0

            info_assignment = "No definido"
            info_exam = "No definido"
            info_interaction = "No definido"
            info_foro = "No definido"

            point_average_assignment = point_average_exam = point_average_interaction = point_average_foro = 0

            if rec.gradebook_id or rec.gradebook_student_id.gradebook_id:
                gradebook = self._get_gradebook_info(rec)

                for result in rec.gradebook_result_ids:
                    if result.survey_type == 'assignment':
                        assignment_total += result.scoring_total
                        assignment_count += 1
                    elif result.survey_type == 'exam':
                        exam_total += result.scoring_total
                        exam_count += 1
                    elif result.survey_type == 'interaction':
                        interaction_total += result.scoring_total
                        interaction_count += 1
                    elif result.survey_type == 'foro':
                        foro_total += result.scoring_total
                        foro_count += 1

                if gradebook['assignment']['qty'] and gradebook['assignment']['weight']:
                    info_assignment = '[ %s de %s ] Peso: %s %%' % (str(assignment_count), str(gradebook['assignment']['qty']), str(gradebook['assignment']['weight']))

                if gradebook['exam']['qty'] and gradebook['exam']['weight']:
                    info_exam = '[ %s de %s ] Peso: %s %%' % (str(exam_count), str(gradebook['exam']['qty']), str(gradebook['exam']['weight']))

                if gradebook['interaction']['qty'] and gradebook['interaction']['weight']:
                    info_interaction = 'Peso: %s %%' % (str(gradebook['interaction']['weight']))

                if gradebook['foro']['qty'] and gradebook['foro']['weight']:
                    info_foro = '[ Req. pub. %s ] Peso: %s %%' % (str(gradebook['foro']['qty']), str(gradebook['foro']['weight']))

                # Fix: promedio parcial en vez de 0 cuando el conteo no
                # coincide con la qty de la plantilla, siempre que haya al
                # menos 1 resultado registrado.
                point_average_assignment = (assignment_total / assignment_count) if assignment_count > 0 else 0
                point_average_exam = (exam_total / exam_count) if exam_count > 0 else 0
                point_average_interaction = interaction_total / interaction_count if 1 == interaction_count and interaction_count > 0 else 0
                point_average_foro = foro_total / foro_count if 1 == foro_count and foro_count > 0 else 0

                rec.info_assignment = info_assignment
                rec.info_exam = info_exam
                rec.info_interaction = info_interaction
                rec.info_foro = info_foro

            # Calcula los promedios
            gradebook_id = rec.gradebook_id or rec.gradebook_student_id.gradebook_id
            round_subject_avg = gradebook_id.round_subject_avg
            if gradebook_id and round_subject_avg:
                point_average_assignment = self.round_custom(point_average_assignment)
                point_average_exam = self.round_custom(point_average_exam)
                point_average_interaction = self.round_custom(point_average_interaction)
                point_average_foro = self.round_custom(point_average_foro)

            rec.point_average_assignment = point_average_assignment
            rec.point_average_exam = point_average_exam
            rec.point_average_interaction = point_average_interaction
            rec.point_average_foro = point_average_foro
