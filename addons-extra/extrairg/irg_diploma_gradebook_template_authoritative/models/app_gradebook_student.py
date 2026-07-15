# -*- coding: utf-8 -*-
import logging

from odoo import api, models


_logger = logging.getLogger(__name__)


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    @api.depends(
        'gradebook_id',
        'gradebook_id.final_calculation_mode',
        'gradebook_subject_ids',
        'gradebook_subject_ids.final_subject_note',
        'gradebook_subject_ids.op_subject_id',
        'gradebook_subject_ids.op_subject_id.name',
        'gradebook_subject_ids.op_subject_id.code',
        'gradebook_subject_ids.op_subject_id.subject_type',
    )
    def _compute_diploma_recovery_required(self):
        return super()._compute_diploma_recovery_required()

    @api.depends(
        'gradebook_id',
        'gradebook_id.final_calculation_mode',
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
    def _amount_prod_final(self):
        """Preserve inherited behavior and apply the explicit mode last."""
        super()._amount_prod_final()
        for gradebook in self:
            diploma_final = gradebook._get_diploma_final_score()
            if diploma_final is not False:
                gradebook.total_final = diploma_final

    @api.depends(
        'student_id',
        'gradebook_id',
        'gradebook_id.final_calculation_mode',
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
        """Preserve inherited behavior and apply the explicit mode last."""
        super().compute_avg_score()
        for gradebook in self:
            diploma_final = gradebook._get_diploma_final_score()
            if diploma_final is not False:
                gradebook.avg_score = diploma_final

    def write(self, values):
        """Make a manually selected template visible immediately.

        The dependency graph already invalidates both computed fields.  The
        explicit calls also cover installations where another addon replaced
        a compute dependency list.  The context key prevents a future write in
        that computation chain from re-entering this block.
        """
        result = super().write(values)
        if (
            'gradebook_id' in values
            and not self.env.context.get(
                'irg_skip_authoritative_gradebook_recompute'
            )
        ):
            gradebooks = self.with_context(
                irg_skip_authoritative_gradebook_recompute=True
            )
            gradebooks.invalidate_recordset(['total_final', 'avg_score'])
            gradebooks._amount_prod_final()
            gradebooks.compute_avg_score()
        return result

    def _get_diploma_weighting_values(self):
        """Return 50/50 inputs when the user selected the Diploma mode.

        The template mode is the functional authority.  Course category, type
        and name are deliberately not consulted here because those secondary
        classifications are inconsistent in the beta database.
        """
        self.ensure_one()
        if not self.gradebook_id:
            return False
        if self.gradebook_id.final_calculation_mode != 'diploma_50_50':
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
            _logger.warning(
                'Authoritative Diploma 50/50 skipped for gradebook %s: '
                'found %s presential subject candidates.',
                self.id,
                len(presencial_subjects),
            )
            return False

        non_presential_subjects = compulsory_subjects - presencial_subjects
        if not non_presential_subjects:
            _logger.warning(
                'Authoritative Diploma 50/50 skipped for gradebook %s: '
                'no ordinary compulsory subjects found.',
                self.id,
            )
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
