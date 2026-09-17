from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError

from .irg_tfm_grade_sync import (
    _TFM_DEFER_GRADE_TRIGGER,
    _TFM_GRADE_SYNC_ORIGIN,
    _TFM_INTERNAL_TOKEN,
)


_TFM_PROGRESS_FIELDS = frozenset({
    'gradebook_subject_id',
    'scoring_total',
    'survey_type',
})
_TFM_PROTECTED_RELATIONSHIP_FIELDS = frozenset({
    'survey_type', 'gradebook_subject_id', 'irg_tfm_thesis_id',
})


class AppGradebookResult(models.Model):
    _inherit = 'app.gradebook.result'

    irg_tfm_thesis_id = fields.Many2one(
        'tesis.model',
        string='Expediente TFM',
        index=True,
        copy=False,
        readonly=True,
        ondelete='restrict',
    )

    _sql_constraints = [(
        'irg_tfm_result_thesis_unique',
        'unique(irg_tfm_thesis_id)',
        'El expediente TFM ya está vinculado a una calificación.',
    )]

    def _irg_tfm_affected_subjects(self):
        return self.mapped('gradebook_subject_id').exists()

    def _irg_tfm_refresh_affected_enrollments(
        self,
        subjects,
        locked_enrollments=None,
    ):
        """Recompute progress and activate only enrollments derived from grades."""
        subjects = subjects.sudo().exists()
        pairs = {
            (
                subject.gradebook_student_id.student_id.id,
                subject.gradebook_student_id.course_id.id,
                subject.gradebook_student_id.batch_id.id,
            )
            for subject in subjects
            if subject.gradebook_student_id.student_id
            and subject.gradebook_student_id.course_id
            and subject.gradebook_student_id.batch_id
        }
        if not pairs:
            return

        student_ids = list({student_id for student_id, _course_id, _batch_id in pairs})
        course_ids = list({course_id for _student_id, course_id, _batch_id in pairs})
        batch_ids = list({batch_id for _student_id, _course_id, batch_id in pairs})
        enrollments = self.env['op.student.course'].sudo().search([
            ('student_id', 'in', student_ids),
            ('course_id', 'in', course_ids),
            ('batch_id', 'in', batch_ids),
            ('course_id.activate_tesis', '=', True),
        ])
        enrollments = enrollments.filtered(
            lambda enrollment: (
                enrollment.student_id.id,
                enrollment.course_id.id,
                enrollment.batch_id.id,
            ) in pairs
        )
        if not enrollments:
            return

        if locked_enrollments is None:
            self.env.cr.execute(
                'SELECT id FROM op_student_course '
                'WHERE id IN %s ORDER BY id FOR UPDATE',
                [tuple(enrollments.ids)],
            )
        else:
            locked_enrollments = locked_enrollments.sudo().exists()
            if not set(enrollments.ids).issubset(locked_enrollments.ids):
                raise ValidationError(_(
                    'La matrícula afectada cambió durante la sincronización TFM.'
                ))
        subjects.compute_final_subject_note()
        subjects.flush_recordset(['final_subject_note'])
        enrollments.invalidate_recordset(['completion_porc'])
        for enrollment in enrollments:
            enrollment._irg_ensure_tfm_record()

    def _irg_tfm_reject_untrusted_sync_context(self):
        context = self.env.context
        forged = (
            _TFM_GRADE_SYNC_ORIGIN in context
            or (
                _TFM_DEFER_GRADE_TRIGGER in context
                and context.get(_TFM_DEFER_GRADE_TRIGGER) is not _TFM_INTERNAL_TOKEN
            )
            or 'irg_tfm_thesis_id' in context
            or 'default_irg_tfm_thesis_id' in context
        )
        if forged:
            raise AccessError(_(
                'Los marcadores y vínculos de sincronización TFM son internos.'
            ))

    def _irg_tfm_reject_public_relationship_values(self, values, creating=False):
        if 'irg_tfm_thesis_id' in values:
            raise AccessError(_('El vínculo TFM solo puede calcularlo el servidor.'))
        protected_updates = (
            _TFM_PROTECTED_RELATIONSHIP_FIELDS.intersection(values)
            if not creating else set()
        )
        if not protected_updates:
            return
        self.env['tesis.model']._irg_tfm_guard_linked_identity(self, 'write')

    @api.model
    def _irg_tfm_materialize_protected_create_defaults(self, values):
        effective_values = dict(values)
        defaults = self.default_get(['irg_tfm_thesis_id'])
        if 'irg_tfm_thesis_id' in defaults:
            raise AccessError(_(
                'El vínculo TFM solo puede calcularlo el servidor.'
            ))
        effective_values['irg_tfm_thesis_id'] = False
        return effective_values

    @api.model
    def _irg_tfm_internal_create(self, values):
        if not self.env.su:
            raise AccessError(_('La creación interna TFM requiere privilegio acotado.'))
        required = {
            'gradebook_subject_id', 'survey_type', 'scoring_total',
            'irg_tfm_thesis_id',
        }
        allowed = required | {'description', 'rated_by'}
        if not required.issubset(values) or not set(values).issubset(allowed):
            raise ValueError('Invalid internal TFM result create payload.')
        return self.with_context(
            **{_TFM_DEFER_GRADE_TRIGGER: _TFM_INTERNAL_TOKEN}
        ).create(dict(values))

    def _irg_tfm_internal_write(self, values):
        if not self.env.su:
            raise AccessError(_('La escritura interna TFM requiere privilegio acotado.'))
        allowed = {'scoring_total', 'irg_tfm_thesis_id'}
        if not values or not set(values).issubset(allowed):
            raise ValueError('Invalid internal TFM result write payload.')
        return self.with_context(
            **{_TFM_DEFER_GRADE_TRIGGER: _TFM_INTERNAL_TOKEN}
        ).write(dict(values))

    def _irg_tfm_reverse_candidate_line(self, line_id, survey_type, linked=False):
        """Safe preliminary lookup: only a non-exam or non-TFM line is ignored.

        Anything that reaches the configured Canal TFM family becomes a TFM
        candidate, and from that point on no resolution, scale, lock or
        integrity error may be swallowed to leave it silently unlinked.  An
        already linked result is always a candidate, so losing the Canal TFM
        configuration can never let the two grades drift apart.
        """
        empty = self.env['app.gradebook.subject'].browse()
        if not line_id or (not linked and survey_type != 'exam'):
            return empty
        try:
            line_id = int(line_id)
        except (TypeError, ValueError):
            return empty
        line = self.env['app.gradebook.subject'].sudo().browse(line_id).exists()
        if not line:
            return empty
        if linked:
            return line
        subject = line.op_subject_id
        channel = line.gradebook_student_id.course_id.irg_tfm_channel_id
        if not subject or not channel:
            return empty
        if subject.slide_channel_id not in channel.sudo()._irg_tfm_family_channels():
            return empty
        return line

    def _irg_tfm_authorize_reverse_parent(self, lines, creating=False):
        """Authorize the actor against the proposed parent before ``super()``."""
        operation = 'create' if creating else 'write'
        self.check_access_rights(operation)
        if not creating:
            self.check_access_rule('write')
        lines = lines.with_env(self.env)
        lines.check_access_rights('read')
        lines.check_access_rule('read')
        return True

    @api.model_create_multi
    def _irg_tfm_create_business(self, vals_list):
        return super(
            AppGradebookResult,
            self.with_context(
                **{_TFM_DEFER_GRADE_TRIGGER: _TFM_INTERNAL_TOKEN}
            ),
        ).create(vals_list)

    def _irg_tfm_write_business(self, values):
        return super(
            AppGradebookResult,
            self.with_context(
                **{_TFM_DEFER_GRADE_TRIGGER: _TFM_INTERNAL_TOKEN}
            ),
        ).write(dict(values))

    @api.model_create_multi
    def create(self, vals_list):
        caller_context = dict(self.env.context)
        caller_context.pop(_TFM_DEFER_GRADE_TRIGGER, None)
        already_deferred = (
            self.env.context.get(_TFM_DEFER_GRADE_TRIGGER)
            is _TFM_INTERNAL_TOKEN
        )
        if already_deferred:
            created = super(AppGradebookResult, self).create(vals_list)
            return self.with_context(caller_context).browse(created.ids)

        self._irg_tfm_reject_untrusted_sync_context()
        prepared = []
        for values in vals_list:
            self._irg_tfm_reject_public_relationship_values(
                values,
                creating=True,
            )
            prepared.append(
                self._irg_tfm_materialize_protected_create_defaults(values)
            )

        created_by_index = {}
        ordinary_indexes = []
        ordinary_vals = []
        candidate_items = []
        for index, values in enumerate(prepared):
            line = self._irg_tfm_reverse_candidate_line(
                values.get('gradebook_subject_id'),
                values.get('survey_type'),
            )
            if line:
                candidate_items.append((index, values, line))
            else:
                ordinary_indexes.append(index)
                ordinary_vals.append(values)

        if ordinary_vals:
            created = self._irg_tfm_create_business(ordinary_vals)
            created._irg_tfm_refresh_affected_enrollments(
                created._irg_tfm_affected_subjects()
            )
            for index, record_id in zip(ordinary_indexes, created.ids):
                created_by_index[index] = record_id

        for index, values, line in candidate_items:
            self._irg_tfm_authorize_reverse_parent(line, creating=True)
            created = self.env['tesis.model']._irg_tfm_sync_gradebook_to_points(
                operation='create',
                actor=self.env.user,
                results=self,
                values=values,
                caller_context=caller_context,
            )
            created_by_index[index] = created.id

        return self.with_context(caller_context).browse(
            [created_by_index[index] for index in range(len(prepared))]
        )

    def write(self, values):
        internally_deferred = (
            self.env.context.get(_TFM_DEFER_GRADE_TRIGGER)
            is _TFM_INTERNAL_TOKEN
        )
        if not internally_deferred:
            self._irg_tfm_reject_untrusted_sync_context()
            self._irg_tfm_reject_public_relationship_values(values)
            if _TFM_PROGRESS_FIELDS.intersection(values):
                candidate_lines = self.env['app.gradebook.subject']
                candidate_records = self.browse()
                for record in self:
                    line = record._irg_tfm_reverse_candidate_line(
                        values.get(
                            'gradebook_subject_id',
                            record.gradebook_subject_id.id,
                        ),
                        values.get('survey_type', record.survey_type),
                        linked=bool(record.irg_tfm_thesis_id),
                    )
                    if line:
                        candidate_lines |= line
                        candidate_records |= record
                if candidate_records and candidate_records != self:
                    raise ValidationError(_(
                        'No se puede sincronizar un conjunto mixto de '
                        'resultados TFM y no TFM; edítelos por separado.'
                    ))
                if candidate_lines:
                    self._irg_tfm_authorize_reverse_parent(candidate_lines)
                    return self.env['tesis.model']._irg_tfm_sync_gradebook_to_points(
                        operation='write',
                        actor=self.env.user,
                        results=self,
                        values=values,
                    )
        should_refresh = (
            not internally_deferred
            and bool(_TFM_PROGRESS_FIELDS.intersection(values))
        )
        previous_subjects = self._irg_tfm_affected_subjects() if should_refresh else self.browse()
        result = super().write(dict(values))
        if should_refresh:
            subjects = previous_subjects | self._irg_tfm_affected_subjects()
            self._irg_tfm_refresh_affected_enrollments(subjects)
        return result

    def unlink(self):
        internally_deferred = (
            self.env.context.get(_TFM_DEFER_GRADE_TRIGGER)
            is _TFM_INTERNAL_TOKEN
        )
        if not internally_deferred:
            self._irg_tfm_reject_untrusted_sync_context()
            self.env['tesis.model']._irg_tfm_guard_linked_identity(self, 'unlink')
        should_refresh = not internally_deferred
        subjects = self._irg_tfm_affected_subjects() if should_refresh else self.browse()
        result = super().unlink()
        if should_refresh:
            self._irg_tfm_refresh_affected_enrollments(subjects)
        return result
