from markupsafe import escape

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError

from .irg_tfm_grade_sync import (
    _TFM_DEFER_GRADE_TRIGGER,
    _TFM_GRADE_SYNC_ORIGIN,
    _TFM_INTERNAL_TOKEN,
)
from .irg_tfm_logic import TfmRuleError, render_outline_text, weighted_points


_COMPONENT_NOTE_FIELDS = (
    'irg_tfm_nota_tutor',
    'irg_tfm_nota_borrador',
    'irg_tfm_nota_defensa',
)
_COMPONENT_SET_FIELDS = {
    'irg_tfm_nota_tutor': 'irg_tfm_nota_tutor_set',
    'irg_tfm_nota_borrador': 'irg_tfm_nota_borrador_set',
    'irg_tfm_nota_defensa': 'irg_tfm_nota_defensa_set',
}
_COMPONENT_KEYS = {
    'tutor': ('irg_tfm_nota_tutor', 'irg_tfm_nota_tutor_set'),
    'draft': ('irg_tfm_nota_borrador', 'irg_tfm_nota_borrador_set'),
    'defense': ('irg_tfm_nota_defensa', 'irg_tfm_nota_defensa_set'),
}


class TesisModel(models.Model):
    _inherit = 'tesis.model'

    irg_tfm_convocation_id = fields.Many2one(
        'irg.tfm.convocatoria',
        string='Convocatoria TFM',
        tracking=True,
        ondelete='restrict',
    )
    irg_tfm_activated_at = fields.Datetime(string='Activado TFM', readonly=True)
    irg_tfm_submission_ids = fields.One2many(
        'irg.tfm.entrega', 'thesis_id', string='Entregas TFM', readonly=True,
    )
    irg_tfm_outline_ids = fields.One2many(
        'irg.tfm.esquema',
        'thesis_id',
        string='Esquemas',
        readonly=True,
        groups='irg_tfm_convocatorias.group_tfm_reviewer',
    )
    irg_tfm_window_ids = fields.One2many(
        'irg.tfm.ventana.alumno',
        'thesis_id',
        string='Ventanas por alumno',
    )
    irg_tfm_nota_tutor = fields.Float(
        string='Nota del tutor',
        digits=(16, 2),
        groups='irg_tfm_convocatorias.group_tfm_reviewer',
    )
    irg_tfm_nota_tutor_set = fields.Boolean(
        groups='irg_tfm_convocatorias.group_tfm_reviewer',
    )
    irg_tfm_nota_borrador = fields.Float(
        string='Nota del borrador',
        digits=(16, 2),
        groups='irg_tfm_convocatorias.group_tfm_reviewer',
    )
    irg_tfm_nota_borrador_set = fields.Boolean(
        groups='irg_tfm_convocatorias.group_tfm_reviewer',
    )
    irg_tfm_nota_defensa = fields.Float(
        string='Nota de defensa',
        digits=(16, 2),
        groups='irg_tfm_convocatorias.group_tfm_reviewer',
    )
    irg_tfm_nota_defensa_set = fields.Boolean(
        groups='irg_tfm_convocatorias.group_tfm_reviewer',
    )

    _sql_constraints = [
        ('irg_tfm_tesis_course_unique', 'unique(course_id)',
         'Solo puede existir una ficha TFM por matrícula.'),
    ]

    def _irg_require_internal_user(self):
        if not self.env.user.has_group('base.group_user'):
            raise AccessError(_('Only internal users can manage TFM convocations.'))

    def _irg_reconcile_tfm_membership(self):
        """Synchronize the eLearning membership for this TFM record."""
        self._irg_require_internal_user()
        self.ensure_one()
        self.env.cr.execute(
            'SELECT id FROM tesis_model WHERE id = %s FOR UPDATE', [self.id]
        )
        self.invalidate_recordset()
        record = self.exists()
        if not record:
            return True
        return self.env['slide.channel.partner']._irg_sync_tfm_membership(record)

    def _irg_has_tfm_outline_submission(self):
        """Use the Task 2 delivery predicate; no other stage satisfies it."""
        self.ensure_one()
        legacy = any(
            submission._irg_is_tfm_outline_submission()
            for submission in self.irg_tfm_submission_ids
        )
        survey_outline = bool(self.env['irg.tfm.esquema'].sudo().search_count([
            ('thesis_id', '=', self.id), ('state', '=', 'done'),
        ]))
        return legacy or survey_outline

    @api.model
    def _irg_portal_student(self, raise_missing=True):
        if self.env.user._is_public():
            if raise_missing:
                raise AccessError(_('Authentication is required.'))
            return self.env['op.student'].browse()
        students = self.env['op.student'].sudo().with_context(active_test=False).search([
            ('user_id', '=', self.env.uid),
        ], limit=2)
        if len(students) == 1 and students.active:
            return students
        if raise_missing:
            raise AccessError(_('Your student profile could not be resolved unambiguously.'))
        return self.env['op.student'].browse()

    @api.model
    def _irg_portal_owned_thesis(self, course_id, raise_missing=True):
        try:
            course_id = int(course_id)
        except (TypeError, ValueError):
            course_id = 0
        student = self._irg_portal_student(raise_missing=raise_missing)
        if not student or not course_id:
            return self.browse()
        enrollments = self.env['op.student.course'].sudo().search([
            ('student_id', '=', student.id),
            ('student_id.user_id', '=', self.env.uid),
            ('course_id', '=', course_id),
        ], limit=2)
        if len(enrollments) != 1:
            if raise_missing:
                raise AccessError(_('Your TFM enrollment could not be resolved unambiguously.'))
            return self.browse()
        theses = self.sudo().search([
            ('course_id', '=', enrollments.id),
            ('course_id.student_id', '=', student.id),
            ('course_id.student_id.user_id', '=', self.env.uid),
            ('course_id.course_id', '=', course_id),
            ('irg_tfm_activated_at', '!=', False),
        ], limit=2)
        if len(theses) != 1:
            if raise_missing:
                raise AccessError(_('Your active TFM record could not be resolved unambiguously.'))
            return self.browse()
        return theses

    def _irg_create_delivery_exception(
        self, stage, raw, filename, declared_mimetype, exception_reason, comment=None,
    ):
        self._irg_require_internal_user()
        self.ensure_one()
        if stage == 'outline':
            raise ValidationError(_(
                'Los nuevos Esquemas se registran mediante el cuestionario TFM.'
            ))
        reason = (exception_reason or '').strip()
        if not reason:
            raise ValidationError(_('An exception reason is required.'))
        Delivery = self.env['irg.tfm.entrega']
        safe_name, mimetype = Delivery._irg_validate_upload(raw, filename, declared_mimetype)
        delivery = Delivery._irg_create_locked_submission(
            self.sudo(),
            stage,
            raw,
            safe_name,
            mimetype,
            comment=comment,
            internal_exception=True,
            exception_reason=reason,
        )
        self.message_post(
            body=_('TFM delivery exception created for %s, version %s. Reason: %s')
            % (stage, delivery.version, escape(reason)),
        )
        return delivery

    @api.model_create_multi
    def create(self, vals_list):
        self._irg_tfm_reject_reserved_public_input(vals_list)
        if any(vals.get('irg_tfm_convocation_id') for vals in vals_list):
            raise ValidationError(
                _('Create the thesis first, then assign its TFM convocation.'),
            )
        prepared_vals, graded_indexes = self._irg_tfm_prepare_grade_create_values(
            vals_list
        )
        if graded_indexes:
            enrollments = self._irg_tfm_grade_create_enrollments(
                prepared_vals,
                graded_indexes,
            )
            actor = self._irg_tfm_require_grade_actor(
                'create',
                enrollments=enrollments,
            )
            return self._irg_tfm_sync_points_to_gradebook(
                operation='create',
                actor=actor,
                values=prepared_vals,
                graded_indexes=graded_indexes,
            )
        return self._irg_tfm_create_business(prepared_vals)

    @api.model_create_multi
    def _irg_tfm_create_business(self, vals_list):
        return super().create(vals_list)

    def _irg_tfm_reject_reserved_public_input(self, values):
        payloads = values if isinstance(values, list) else [values]
        context = self.env.context
        forged_context = (
            _TFM_GRADE_SYNC_ORIGIN in context
            or (
                _TFM_DEFER_GRADE_TRIGGER in context
                and context.get(_TFM_DEFER_GRADE_TRIGGER) is not _TFM_INTERNAL_TOKEN
            )
            or 'irg_tfm_thesis_id' in context
            or 'default_irg_tfm_thesis_id' in context
        )
        forged_payload = any(
            'irg_tfm_thesis_id' in payload for payload in payloads
        )
        if forged_context or forged_payload:
            raise AccessError(_(
                'Los marcadores y vínculos de sincronización TFM son internos.'
            ))

    def _irg_tfm_prepare_grade_create_values(self, vals_list):
        missing_grade = any('points_fin' not in values for values in vals_list)
        effective_defaults = (
            self.default_get(['points_fin']) if missing_grade else {}
        )
        prepared = []
        graded_indexes = []
        for index, original in enumerate(vals_list):
            values = dict(original)
            grade_was_supplied = 'points_fin' in values
            if (
                'points_fin' not in values
                and 'points_fin' in effective_defaults
            ):
                values['points_fin'] = effective_defaults['points_fin']
                grade_was_supplied = True
            elif 'points_fin' not in values:
                values['points_fin'] = 0.0
            if grade_was_supplied:
                graded_indexes.append(index)
            prepared.append(values)
        return prepared, graded_indexes

    def _irg_tfm_grade_create_enrollments(self, vals_list, graded_indexes):
        enrollment_ids = []
        for index in graded_indexes:
            raw_id = vals_list[index].get('course_id')
            try:
                enrollment_id = int(raw_id)
            except (TypeError, ValueError):
                raise ValidationError(_('La matrícula TFM indicada no es válida.'))
            if enrollment_id <= 0:
                raise ValidationError(_('La matrícula TFM indicada no es válida.'))
            enrollment_ids.append(enrollment_id)
        enrollments = self.env['op.student.course'].browse(
            sorted(set(enrollment_ids))
        ).exists()
        if set(enrollments.ids) != set(enrollment_ids):
            raise ValidationError(_('La matrícula TFM indicada no es válida.'))
        return enrollments

    def _irg_tfm_require_grade_actor(self, operation, enrollments=None):
        actor = self.env.user
        if not actor.has_group('irg_tfm_convocatorias.group_tfm_reviewer'):
            raise AccessError(_('Solo un Revisor TFM puede modificar la nota final.'))
        self.check_access_rights(operation)
        if operation == 'write':
            self.check_access_rule('write')
        if enrollments:
            enrollments.check_access_rights('read')
            enrollments.check_access_rule('read')
        return actor

    def _irg_tfm_points_from_components(self, values):
        """Calcula el punteo solo cuando las tres notas ya fueron informadas."""
        self.ensure_one()
        notes = {}
        for key, (note_field, set_field) in _COMPONENT_KEYS.items():
            is_set = values[set_field] if set_field in values else getattr(self, set_field)
            if not is_set:
                return None
            notes[key] = values[note_field] if note_field in values else getattr(self, note_field)
        convocation = self.irg_tfm_convocation_id
        if not convocation:
            raise ValidationError(_(
                'Asigna una convocatoria antes de calcular el punteo final.'
            ))
        weights = {
            'tutor': convocation.weight_tutor,
            'draft': convocation.weight_draft,
            'defense': convocation.weight_defense,
        }
        try:
            points = weighted_points(notes, weights)
        except TfmRuleError as exc:
            if str(exc) == 'weights':
                raise ValidationError(_(
                    'Las ponderaciones de la convocatoria deben sumar 100.'
                )) from exc
            raise ValidationError(_(
                'La nota TFM debe ser 0 o un número finito entre 1 y 10.'
            )) from exc
        try:
            self._irg_tfm_validate_score(points)
        except ValidationError as exc:
            raise ValidationError(_(
                'La nota ponderada (%s) debe ser 0 o estar entre 1 y 10.'
            ) % points) from exc
        return points

    def _send_email_notification(self):
        if self.env.context.get('irg_tfm_auto_activation'):
            return True
        return super()._send_email_notification()

    def write(self, vals):
        self._irg_tfm_reject_reserved_public_input(vals)
        if 'course_id' in vals and 'irg_tfm_convocation_id' in vals:
            raise ValidationError(_(
                'Cambie la matrícula y la convocatoria TFM en operaciones separadas.'
            ))
        if 'course_id' in vals:
            self.env['tesis.model']._irg_tfm_guard_linked_identity(self, 'write')
        if 'points_fin' in vals and any(name in vals for name in _COMPONENT_NOTE_FIELDS):
            raise ValidationError(_(
                'El punteo final se calcula con las tres notas. No lo escribas a mano en la misma operación.'
            ))
        if any(name in vals for name in _COMPONENT_SET_FIELDS.values()):
            raise AccessError(_('Los indicadores de nota TFM son internos.'))
        if 'points_fin' in vals:
            actor = self._irg_tfm_require_grade_actor('write')
            return self._irg_tfm_sync_points_to_gradebook(
                operation='write',
                actor=actor,
                values=dict(vals),
            )
        touched = [name for name in _COMPONENT_NOTE_FIELDS if name in vals]
        if touched:
            if len(self) != 1:
                for record in self:
                    record.write(dict(vals))
                return True
            actor = self._irg_tfm_require_grade_actor('write')
            prepared = dict(vals)
            for name in touched:
                self._irg_tfm_validate_score(prepared[name])
                prepared[_COMPONENT_SET_FIELDS[name]] = True
            points = self._irg_tfm_points_from_components(prepared)
            if points is not None:
                prepared['points_fin'] = points
                return self._irg_tfm_sync_points_to_gradebook(
                    operation='write',
                    actor=actor,
                    values=prepared,
                )
            return self._irg_tfm_write_business(prepared)
        return self._irg_tfm_write_business(vals)

    def unlink(self):
        self.env['tesis.model']._irg_tfm_guard_linked_identity(self, 'unlink')
        return super().unlink()

    def _irg_tfm_write_business(self, vals):
        if 'irg_tfm_convocation_id' not in vals:
            return super().write(vals)

        # This permission check is intentionally before locking, rereading, or
        # any future sudo use: UI restrictions must not be the authorization.
        self._irg_require_internal_user()
        convocation_id = vals.get('irg_tfm_convocation_id')
        if convocation_id:
            try:
                convocation_id = int(convocation_id)
            except (TypeError, ValueError):
                raise ValidationError(_('The selected TFM convocation is invalid.'))
            vals = dict(vals, irg_tfm_convocation_id=convocation_id)

        # Lock mutable configuration before the theses.  ``op.course.write``
        # already obtains the course row lock through UPDATE before reconciling
        # (and therefore before locking a thesis), so this common order avoids
        # course/thesis lock inversions.  Convocation rows are locked first and
        # every multi-row query has a deterministic id order.
        course_ids = sorted(set(self.mapped('course_id.course_id').ids))
        if convocation_id:
            self.env.cr.execute(
                'SELECT id FROM irg_tfm_convocatoria WHERE id = %s FOR UPDATE',
                [convocation_id],
            )
            if not self.env.cr.fetchone():
                raise ValidationError(_('The selected TFM convocation is invalid.'))
        if course_ids:
            self.env.cr.execute(
                'SELECT id FROM op_course WHERE id IN %s ORDER BY id FOR UPDATE',
                [tuple(course_ids)],
            )
        ids = self.ids
        if ids:
            self.env.cr.execute(
                'SELECT id FROM tesis_model WHERE id IN %s ORDER BY id FOR UPDATE',
                [tuple(sorted(ids))],
            )
        self.invalidate_recordset()
        records = self.exists()
        current_courses = records.mapped('course_id.course_id')
        current_course_ids = set(current_courses.ids)
        if not current_course_ids.issubset(course_ids):
            raise ValidationError(_(
                'The TFM course changed concurrently; retry the convocation assignment.'
            ))
        current_courses.invalidate_recordset(['irg_tfm_channel_id'])
        if convocation_id:
            convocation = self.env['irg.tfm.convocatoria'].browse(convocation_id)
            convocation.invalidate_recordset(['active'])
            convocation = convocation.exists()
            if not convocation or not convocation.active:
                raise ValidationError(_('An archived TFM convocation cannot be assigned.'))
            for record in records:
                configured_channel = record.course_id.course_id.irg_tfm_channel_id
                effective_channel = (
                    configured_channel._irg_tfm_effective_channel(record.course_id)
                    if configured_channel else self.env['slide.channel']
                )
                if not effective_channel:
                    raise ValidationError(_(
                        'The enrollment must have an available TFM eLearning channel '
                        'for its HomeClass or Online modality before assigning a convocation.'
                    ))
        result = super(TesisModel, records).write(vals)
        for record in records:
            if record.irg_tfm_convocation_id:
                record.message_post(
                    body=_('TFM convocation assigned: %s.')
                    % record.irg_tfm_convocation_id.display_name,
                )
                if not record._irg_has_tfm_outline_submission():
                    record.message_post(
                        body=_('Warning: this TFM has no outline submission yet.'),
                    )
            else:
                record.message_post(body=_('TFM convocation removed; outline submissions are available again.'))
            record._irg_reconcile_tfm_membership()
        return result
