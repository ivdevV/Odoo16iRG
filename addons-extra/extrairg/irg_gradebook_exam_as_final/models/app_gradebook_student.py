# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    def state_to_done(self):
        """Override state_to_done to bypass the assignment validation.

        Since irg_gradebook_exam_as_final establishes that the final subject
        grade is derived exclusively from exam results, requiring a specific
        number of assignments before closing the gradebook is inconsistent.
        This override removes only the assignment-count check; all other
        validations (exam qty, interaction, foro) are preserved.
        """
        for rec in self:
            if not rec.gradebook_id:
                # Keep original guard (note: original has a bug — no raise — we keep it)
                UserError(_('"Calificaciones template" es obligatorio.'))
            for subject in rec.gradebook_subject_ids:
                gradebook = subject._get_gradebook_info(subject)
                if gradebook:
                    qty_examn = len(
                        subject.gradebook_result_ids.filtered(
                            lambda x: x.survey_type == 'exam'
                        )
                    )
                    if gradebook['exam']['qty'] != qty_examn and subject.show_exam:
                        raise UserError(
                            '%s: Tiene %s evaluaciones de tipo "Examen" pero necesita %s.'
                            % (subject.name, qty_examn, gradebook['exam']['qty'])
                        )

                    # ── Assignment validation intentionally removed ──────────────
                    # irg_gradebook_exam_as_final: the final grade is exam-only,
                    # so we do not require assignments to be present.

                    qty_interaction = len(
                        subject.gradebook_result_ids.filtered(
                            lambda x: x.survey_type == 'interaction'
                        )
                    )
                    if qty_interaction != 1 and subject.show_interaction:
                        raise UserError(
                            '%s: Debe tener 1 evaluacion de tipo "Interaccion".'
                            % subject.name
                        )

                    qty_foro = len(
                        subject.gradebook_result_ids.filtered(
                            lambda x: x.survey_type == 'foro'
                        )
                    )
                    if qty_foro != 1 and subject.show_foro:
                        raise UserError(
                            '%s: Debe tener 1 evaluacion de tipo "Foro".'
                            % subject.name
                        )

            rec.state = 'done'
