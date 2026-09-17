import math

from markupsafe import escape
from psycopg2 import sql

from odoo import _, models
from odoo.exceptions import AccessError, ValidationError


_TFM_DEFER_GRADE_TRIGGER = 'irg_tfm_defer_grade_trigger'
_TFM_GRADE_SYNC_ORIGIN = 'irg_tfm_grade_sync_origin'
_TFM_INTERNAL_TOKEN = object()

_TFM_GRADE_LOCK_PHASES = (
    "op_student_course",
    "tesis_model",
    "app_gradebook_student",
    "app_gradebook_subject",
    "app_gradebook_result",
)

# The guards must also serialize the admission, which carries the student,
# course and batch identity of a gradebook.  It is inserted right after the
# enrollment so the phase order of the coordinators stays a subsequence of it.
_TFM_LINK_GUARD_LOCK_PHASES = (
    _TFM_GRADE_LOCK_PHASES[0],
    "op_admission",
) + _TFM_GRADE_LOCK_PHASES[1:]

_TFM_SUBJECT_ERROR = _(
    'Debe existir una única asignatura del curso vinculada al Canal TFM.'
)
_TFM_GRADEBOOK_ERROR = _(
    'No se encontró una única libreta para el alumno, curso y lote.'
)
_TFM_LINE_ERROR = _(
    'La libreta no contiene una única línea para la asignatura TFM.'
)
_TFM_EXAM_ERROR = _(
    'La asignatura TFM contiene varios exámenes sin vínculo; solicite una '
    'corrección autorizada de la configuración antes de continuar.'
)
_TFM_NORMALIZATION_ERROR = _(
    'La escala, precisión o límites de la libreta transformarían la nota TFM; '
    'corrija la plantilla para conservar exactamente la calificación solicitada.'
)
_TFM_CONCURRENT_MAPPING_ERROR = _(
    'La configuración TFM cambió durante la operación; vuelva a intentarlo.'
)
_TFM_ENROLLMENT_ERROR = _(
    'No se encontró una única matrícula para el alumno, curso y lote de la libreta.'
)
_TFM_THESIS_ERROR = _(
    'No se encontró un único expediente TFM activo para la matrícula de la libreta.'
)
_TFM_LINKED_EXAM_ERROR = _(
    'La asignatura TFM ya tiene su calificación vinculada al expediente; '
    'edite ese resultado en lugar de crear otro examen.'
)
_TFM_LINKED_IDENTITY_ERROR = _(
    'No se puede modificar ni eliminar la identidad de una calificación TFM '
    'vinculada; solicite una corrección autorizada de la configuración.'
)
_TFM_SAVEPOINT_ERROR = _(
    'La sincronización inversa TFM solo puede aplicarla su coordinador privado.'
)
_TFM_REVERSE_ADOPTION_ERROR = _(
    'Solo se sincroniza un examen ya registrado en la línea TFM; no se puede '
    'convertir ni mover otro resultado a la calificación TFM.'
)


class _TfmSyncSavepoint:
    """Non-forgeable proof that a private TFM coordinator owns an open savepoint.

    RPC payloads carry JSON only, so no client can construct this object.  The
    inverse primitive therefore cannot be reached from outside the coordinator,
    and no context key ever substitutes for it.
    """

    __slots__ = ('_cursor', '_open')

    def __init__(self, cursor):
        self._cursor = cursor
        self._open = True

    def close(self):
        self._open = False

    def assert_open(self, cursor):
        if not self._open or cursor is not self._cursor:
            raise AccessError(_TFM_SAVEPOINT_ERROR)
        return True


class TesisGradeSync(models.Model):
    _inherit = 'tesis.model'

    def _irg_tfm_resolve_subject(self):
        self.ensure_one()
        course = self.course_id.course_id
        channel = course.irg_tfm_channel_id
        if not channel:
            raise ValidationError(_('El curso no tiene configurado Canal TFM.'))
        family = channel.sudo()._irg_tfm_family_channels()
        subjects = course.subject_ids.filtered(
            lambda subject: subject.slide_channel_id in family
        )
        if len(subjects) != 1:
            raise ValidationError(_TFM_SUBJECT_ERROR)
        return subjects

    def _irg_tfm_resolve_subject_for_enrollment(self, enrollment):
        enrollment.ensure_one()
        course = enrollment.course_id
        channel = course.irg_tfm_channel_id
        if not channel:
            raise ValidationError(_('El curso no tiene configurado Canal TFM.'))
        family = channel.sudo()._irg_tfm_family_channels()
        subjects = course.subject_ids.filtered(
            lambda subject: subject.slide_channel_id in family
        )
        if len(subjects) != 1:
            raise ValidationError(_TFM_SUBJECT_ERROR)
        return subjects

    def _irg_tfm_resolve_grade_line_for_enrollment(self, enrollment, subject):
        enrollment.ensure_one()
        subject.ensure_one()
        gradebooks = self.env['app.gradebook.student'].sudo().search([
            ('admission_id.student_id', '=', enrollment.student_id.id),
            ('admission_id.course_id', '=', enrollment.course_id.id),
            ('admission_id.batch_id', '=', enrollment.batch_id.id),
        ], order='id', limit=2)
        if len(gradebooks) != 1:
            raise ValidationError(_TFM_GRADEBOOK_ERROR)
        lines = gradebooks.gradebook_subject_ids.filtered(
            lambda line: line.op_subject_id == subject
        )
        if len(lines) != 1:
            raise ValidationError(_TFM_LINE_ERROR)
        return lines

    def _irg_tfm_resolve_grade_target(self):
        self.ensure_one()
        subject = self._irg_tfm_resolve_subject()
        return self._irg_tfm_resolve_grade_line_for_enrollment(
            self.course_id,
            subject,
        )

    def _irg_tfm_validate_score(self, value):
        try:
            valid = math.isfinite(value) and (
                value == 0 or 1 <= value <= 10
            )
        except (TypeError, ValueError, OverflowError):
            valid = False
        if not valid:
            raise ValidationError(_(
                'La nota TFM debe ser 0 o un número finito entre 1 y 10.'
            ))

    def _irg_tfm_validate_normalization(self, line, value):
        self._irg_tfm_validate_score(value)
        line.invalidate_recordset([
            'gradebook_id',
            'gradebook_student_id',
        ])
        gradebook = line.gradebook_id or line.gradebook_student_id.gradebook_id
        if not gradebook:
            raise ValidationError(_TFM_NORMALIZATION_ERROR)
        gradebook.invalidate_recordset([
            'grading_scale',
            'round_subject_result',
            'gradebook_template_ids',
        ])
        try:
            scale_is_finite = math.isfinite(gradebook.grading_scale)
        except (TypeError, ValueError, OverflowError):
            scale_is_finite = False
        if not scale_is_finite:
            raise ValidationError(_TFM_NORMALIZATION_ERROR)

        effective = value
        if gradebook.round_subject_result:
            if value - int(value) >= 0.5:
                effective = math.ceil(value)
            else:
                effective = math.floor(value)
        if effective > gradebook.grading_scale:
            effective = gradebook.grading_scale
        if effective != value:
            raise ValidationError(_TFM_NORMALIZATION_ERROR)

    def _irg_tfm_resolve_grade_identity(self, enrollment, thesis=None):
        enrollment = enrollment.sudo().exists()
        enrollment.ensure_one()
        thesis = (thesis or self.browse()).sudo().exists()
        if thesis:
            thesis.ensure_one()
            if thesis.course_id != enrollment:
                raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
            if not thesis.irg_tfm_activated_at:
                raise ValidationError(_(
                    'Solo se puede calificar un expediente TFM activo.'
                ))

        subject = self._irg_tfm_resolve_subject_for_enrollment(enrollment)
        line = self._irg_tfm_resolve_grade_line_for_enrollment(
            enrollment,
            subject,
        )
        gradebook = line.gradebook_student_id
        Result = self.env['app.gradebook.result'].sudo()
        line_results = Result.search([
            ('gradebook_subject_id', '=', line.id),
        ], order='id')
        linked = Result.browse()
        if thesis:
            linked = Result.search([
                ('irg_tfm_thesis_id', '=', thesis.id),
            ], order='id', limit=2)
            if len(linked) > 1:
                raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
            if linked and (
                linked.gradebook_subject_id != line
                or linked.survey_type != 'exam'
            ):
                raise ValidationError(_(
                    'La calificación vinculada no corresponde a la asignatura TFM.'
                ))

        all_results = Result.browse(sorted(set(line_results.ids + linked.ids)))
        candidate = linked
        if not candidate:
            exams = line_results.filtered(lambda result: result.survey_type == 'exam')
            if len(exams) > 1:
                raise ValidationError(_TFM_EXAM_ERROR)
            if exams and exams.irg_tfm_thesis_id:
                raise ValidationError(_(
                    'El examen TFM está vinculado a otro expediente; solicite una '
                    'corrección autorizada de la configuración antes de continuar.'
                ))
            candidate = exams

        identity = {
            'enrollment': enrollment,
            'thesis': thesis,
            'subject': subject,
            'gradebook': gradebook,
            'line': line,
            'results': all_results,
            'candidate': candidate,
        }
        identity['fingerprint'] = self._irg_tfm_identity_fingerprint(identity)
        identity['mapping_fingerprint'] = self._irg_tfm_identity_fingerprint(
            identity,
            result_scores=False,
        )
        identity['thesis_fingerprint'] = (
            (
                thesis.id,
                thesis.course_id.id,
                bool(thesis.irg_tfm_activated_at),
            )
            if thesis else None
        )
        return identity

    def _irg_tfm_identity_fingerprint(self, identity, result_scores=True):
        enrollment = identity['enrollment']
        course = enrollment.course_id
        batch = enrollment.batch_id
        course_subjects = course.subject_ids.sorted('id')
        configured_channel = course.irg_tfm_channel_id
        family = self.env['slide.channel']
        if configured_channel:
            family = configured_channel.sudo()._irg_tfm_family_channels()
        channels = (
            configured_channel
            | family
            | course_subjects.mapped('slide_channel_id')
        ).sorted('id')
        gradebook = identity['gradebook']
        admission = gradebook.admission_id
        lines = gradebook.gradebook_subject_ids.sorted('id')
        line = identity['line']
        effective_template = line.gradebook_id or gradebook.gradebook_id
        results = identity['results'].sorted('id')
        return (
            enrollment.id,
            enrollment.student_id.id,
            course.id,
            batch.id,
            batch.course_id.id,
            batch.code,
            configured_channel.id,
            tuple(subject.id for subject in course_subjects),
            tuple(
                (
                    subject.id,
                    subject.course_id.id,
                    subject.slide_channel_id.id,
                    subject.gradebook_id.id,
                )
                for subject in course_subjects
            ),
            tuple(family.sorted('id').ids),
            tuple(
                (
                    channel.id,
                    channel.irg_homeclass_channel_id.id,
                    channel.irg_online_channel_id.id,
                )
                for channel in channels
            ),
            identity['subject'].id,
            gradebook.id,
            admission.id,
            admission.student_id.id,
            admission.course_id.id,
            admission.batch_id.id,
            gradebook.gradebook_id.id,
            tuple(
                (
                    gradebook_line.id,
                    gradebook_line.gradebook_student_id.id,
                    gradebook_line.op_subject_id.id,
                    gradebook_line.gradebook_id.id,
                )
                for gradebook_line in lines
            ),
            line.id,
            line.gradebook_student_id.id,
            line.op_subject_id.id,
            effective_template.id,
            effective_template.grading_scale,
            bool(effective_template.round_subject_result),
            tuple(
                (
                    result.id,
                    result.gradebook_subject_id.id,
                    result.survey_type,
                    result.irg_tfm_thesis_id.id,
                ) + ((result.scoring_total,) if result_scores else ())
                for result in results
            ),
            identity['candidate'].id,
        )

    def _irg_tfm_assert_same_identity(self, before, after):
        fingerprint_changed = before['fingerprint'] != after['fingerprint']
        thesis_changed = (
            before['thesis_fingerprint'] is not None
            and before['thesis_fingerprint'] != after['thesis_fingerprint']
        )
        if fingerprint_changed or thesis_changed:
            raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)

    def _irg_tfm_assert_same_mapping(self, before, after, new_results=None):
        """Compare the mapping when the gradebook side has already been mutated.

        The propagated score is the one thing this coordinator just changed, so
        it is compared separately by exact equality instead of being part of the
        snapshot.  Everything else, including the row created by this very
        operation, must still match the locked identity.
        """
        new_results = new_results or self.env['app.gradebook.result'].browse()
        comparable = dict(after)
        if new_results:
            if not set(new_results.ids).issubset(after['results'].ids):
                raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
            if after['candidate'].ids != new_results.ids:
                raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
            comparable['results'] = after['results'] - new_results
            comparable['candidate'] = before['candidate']
        if self._irg_tfm_identity_fingerprint(
            comparable,
            result_scores=False,
        ) != before['mapping_fingerprint']:
            raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
        if before['thesis_fingerprint'] != after['thesis_fingerprint']:
            raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
        return True

    def _irg_tfm_lock_rows(self, table, record_ids):
        if table not in _TFM_LINK_GUARD_LOCK_PHASES:
            raise ValueError('Unsupported TFM lock table: %s' % table)
        record_ids = sorted(set(record_ids))
        if not record_ids:
            return
        query = sql.SQL(
            'SELECT id FROM {} WHERE id IN %s ORDER BY id FOR UPDATE'
        ).format(sql.Identifier(table))
        self.env.cr.execute(query, [tuple(record_ids)])
        locked_ids = [row[0] for row in self.env.cr.fetchall()]
        if locked_ids != record_ids:
            raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)

    def _irg_tfm_lock_identities(self, identities, extra_theses=None):
        extra_theses = extra_theses or self.browse()
        enrollment_ids = []
        thesis_ids = list(extra_theses.ids)
        gradebook_ids = []
        line_ids = []
        result_ids = []
        for identity in identities:
            enrollment_ids.extend(identity['enrollment'].ids)
            thesis_ids.extend(identity['thesis'].ids)
            gradebook_ids.extend(identity['gradebook'].ids)
            line_ids.extend(identity['line'].ids)
            result_ids.extend(identity['results'].ids)
        lock_sets = {
            'op_student_course': enrollment_ids,
            'tesis_model': thesis_ids,
            'app_gradebook_student': gradebook_ids,
            'app_gradebook_subject': line_ids,
            'app_gradebook_result': result_ids,
        }
        for table in _TFM_GRADE_LOCK_PHASES:
            self._irg_tfm_lock_rows(table, lock_sets[table])

    def _irg_tfm_invalidate_identity(self, identity=None):
        self.env['op.student.course'].sudo().invalidate_model([
            'student_id', 'course_id', 'batch_id',
        ])
        self.env['tesis.model'].sudo().invalidate_model([
            'course_id', 'irg_tfm_activated_at', 'points_fin',
        ])
        self.env['op.course'].sudo().invalidate_model([
            'irg_tfm_channel_id', 'subject_ids', 'gradebook_id',
        ])
        self.env['op.subject'].sudo().invalidate_model([
            'course_id', 'slide_channel_id', 'gradebook_id',
        ])
        self.env['slide.channel'].sudo().invalidate_model([
            'irg_homeclass_channel_id', 'irg_online_channel_id',
        ])
        self.env['op.batch'].sudo().invalidate_model(['course_id', 'code'])
        self.env['op.admission'].sudo().invalidate_model([
            'student_id', 'course_id', 'batch_id',
        ])
        self.env['app.gradebook.student'].sudo().invalidate_model([
            'admission_id', 'student_id', 'course_id', 'batch_id',
            'gradebook_subject_ids', 'gradebook_id',
        ])
        self.env['app.gradebook.subject'].sudo().invalidate_model([
            'gradebook_student_id', 'op_subject_id', 'gradebook_id',
            'gradebook_result_ids',
        ])
        self.env['app.gradebook.result'].sudo().invalidate_model([
            'gradebook_subject_id', 'survey_type', 'scoring_total',
            'irg_tfm_thesis_id',
        ])
        self.env['app.gradebook'].sudo().invalidate_model([
            'grading_scale', 'round_subject_result', 'gradebook_template_ids',
        ])

    def _irg_tfm_reresolve_after_locks(self, identity):
        self._irg_tfm_invalidate_identity(identity)
        enrollment = self.env['op.student.course'].sudo().browse(
            identity['enrollment'].id
        ).exists()
        thesis = self.sudo().browse(identity['thesis'].ids).exists()
        refreshed = self._irg_tfm_resolve_grade_identity(enrollment, thesis)
        self._irg_tfm_assert_same_identity(identity, refreshed)
        return refreshed

    def _irg_tfm_reresolve_reverse_after_mutation(self, identity, new_results=None):
        """Revalidate the locked mapping after the gradebook side already moved."""
        self._irg_tfm_invalidate_identity()
        enrollment = self.env['op.student.course'].sudo().browse(
            identity['enrollment'].id
        ).exists()
        thesis = self.sudo().browse(identity['thesis'].ids).exists()
        refreshed = self._irg_tfm_resolve_grade_identity(enrollment, thesis)
        self._irg_tfm_assert_same_mapping(identity, refreshed, new_results=new_results)
        return refreshed

    def _irg_tfm_apply_forward_result(self, identity, value, actor):
        thesis = identity['thesis']
        thesis.ensure_one()
        result = identity['candidate']
        old_result_score = result.scoring_total if result else None
        result_changed = False
        link_changed = False

        if not result:
            if value == 0:
                return {
                    'result': result,
                    'old_result_score': None,
                    'result_changed': False,
                    'link_changed': False,
                }
            result = self.env['app.gradebook.result'].sudo()._irg_tfm_internal_create({
                'description': _('Calificación final TFM'),
                'gradebook_subject_id': identity['line'].id,
                'survey_type': 'exam',
                'scoring_total': value,
                'irg_tfm_thesis_id': thesis.id,
                'rated_by': actor.partner_id.id,
            })
            result_changed = True
            link_changed = True
        else:
            result_values = {}
            if not result.irg_tfm_thesis_id:
                result_values['irg_tfm_thesis_id'] = thesis.id
                link_changed = True
            if result.scoring_total != value:
                result_values['scoring_total'] = value
            if result_values:
                result.sudo()._irg_tfm_internal_write(result_values)
                result_changed = True

        result.invalidate_recordset([
            'gradebook_subject_id', 'survey_type', 'scoring_total',
            'irg_tfm_thesis_id',
        ])
        result = self.env['app.gradebook.result'].sudo().browse(result.id).exists()
        if not result or (
            result.irg_tfm_thesis_id != thesis
            or result.gradebook_subject_id != identity['line']
            or result.survey_type != 'exam'
        ):
            raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
        if result.scoring_total != value:
            raise ValidationError(_TFM_NORMALIZATION_ERROR)
        return {
            'result': result,
            'old_result_score': old_result_score,
            'result_changed': result_changed,
            'link_changed': link_changed,
        }

    def _irg_tfm_audit_forward(self, thesis, actor, old_points, value, result_state):
        result = result_state['result']
        if not result:
            return
        effective_change = (
            old_points != value
            or result_state['result_changed']
            or result_state['link_changed']
        )
        if not effective_change:
            return
        old_result = result_state['old_result_score']
        old_result_label = (
            'sin resultado' if old_result is None else str(old_result)
        )
        actor_label = str(escape(actor.display_name))
        result_label = str(escape(result.display_name or ''))
        body = _(
            'Sincronización de nota TFM: actor=%(actor)s (uid=%(uid)s); '
            'origen=thesis; tesis=%(old_thesis)s→%(new)s; '
            'libreta=%(old_result)s→%(new)s; nuevo=%(new)s; '
            'resultado=%(result_id)s (%(result)s).'
        ) % {
            'actor': actor_label,
            'uid': actor.id,
            'old_thesis': old_points,
            'old_result': old_result_label,
            'new': value,
            'result_id': result.id,
            'result': result_label,
        }
        thesis.with_user(actor).message_post(body=body)

    def _irg_tfm_refresh_forward_changes(self, states, locked_enrollments):
        changed_lines = self.env['app.gradebook.subject']
        for identity, result_state in states:
            if result_state['result_changed'] or result_state['link_changed']:
                changed_lines |= identity['line']
        if changed_lines:
            self.env['app.gradebook.result'].sudo()._irg_tfm_refresh_affected_enrollments(
                changed_lines,
                locked_enrollments=locked_enrollments,
            )

    def _irg_tfm_sync_points_to_gradebook(
        self,
        operation,
        actor,
        values,
        graded_indexes=None,
    ):
        if operation == 'create':
            return self._irg_tfm_coordinate_forward_create(
                values,
                graded_indexes or [],
                actor,
            )
        if operation == 'write':
            return self._irg_tfm_coordinate_forward_write(values, actor)
        raise ValueError('Unsupported TFM grade operation: %s' % operation)

    def _irg_tfm_coordinate_forward_create(self, vals_list, graded_indexes, actor):
        with self.env.cr.savepoint():
            entries = []
            enrollment_ids = []
            for index in graded_indexes:
                values = vals_list[index]
                value = values['points_fin']
                self._irg_tfm_validate_score(value)
                if not values.get('irg_tfm_activated_at'):
                    raise ValidationError(_(
                        'Solo se puede calificar un expediente TFM activo.'
                    ))
                enrollment_id = values.get('course_id')
                enrollment = self.env['op.student.course'].sudo().browse(
                    enrollment_id
                ).exists()
                if not enrollment:
                    raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
                identity = self._irg_tfm_resolve_grade_identity(enrollment)
                self._irg_tfm_validate_normalization(identity['line'], value)
                entries.append({
                    'index': index,
                    'value': value,
                    'identity': identity,
                })
                enrollment_ids.append(enrollment.id)

            existing_theses = self.sudo().search([
                ('course_id', 'in', enrollment_ids),
            ], order='id')
            self._irg_tfm_lock_identities(
                [entry['identity'] for entry in entries],
                extra_theses=existing_theses,
            )
            existing_theses.invalidate_recordset(['course_id'])
            existing_after = self.sudo().search([
                ('course_id', 'in', enrollment_ids),
            ], order='id')
            if existing_after.ids != existing_theses.ids:
                raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
            if existing_after:
                raise ValidationError(_('Ya existe un expediente TFM para la matrícula.'))

            for entry in entries:
                refreshed = self._irg_tfm_reresolve_after_locks(entry['identity'])
                self._irg_tfm_validate_normalization(
                    refreshed['line'],
                    entry['value'],
                )
                entry['identity'] = refreshed

            records = self.with_user(actor)._irg_tfm_create_business(vals_list)
            sync_states = []
            for entry in entries:
                thesis = records[entry['index']].sudo()
                refreshed = self._irg_tfm_resolve_grade_identity(
                    thesis.course_id,
                    thesis,
                )
                self._irg_tfm_assert_same_identity(
                    entry['identity'],
                    refreshed,
                )
                result_state = self._irg_tfm_apply_forward_result(
                    refreshed,
                    entry['value'],
                    actor,
                )
                sync_states.append((
                    refreshed,
                    result_state,
                    0.0,
                    entry['value'],
                ))

            locked_enrollments = self.env['op.student.course'].sudo().browse(
                sorted(set(enrollment_ids))
            )
            self._irg_tfm_refresh_forward_changes(
                [
                    (identity, state)
                    for identity, state, _old, _value in sync_states
                ],
                locked_enrollments,
            )
            for identity, result_state, old_points, value in sync_states:
                identity['thesis'].invalidate_recordset(['points_fin'])
                if identity['thesis'].points_fin != value:
                    raise ValidationError(_TFM_NORMALIZATION_ERROR)
                linked_result = result_state['result']
                if linked_result and linked_result.scoring_total != value:
                    raise ValidationError(_TFM_NORMALIZATION_ERROR)
                self._irg_tfm_audit_forward(
                    identity['thesis'],
                    actor,
                    old_points,
                    value,
                    result_state,
                )
            return records

    def _irg_tfm_coordinate_forward_write(self, values, actor):
        value = values['points_fin']
        with self.env.cr.savepoint():
            if {'course_id', 'irg_tfm_convocation_id'}.intersection(values):
                raise ValidationError(_(
                    'Cambie la identidad o convocatoria TFM en una operación '
                    'separada de la nota.'
                ))
            self._irg_tfm_validate_score(value)
            records = self.sudo().exists()
            if set(records.ids) != set(self.ids):
                raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
            entries = []
            for thesis in records.sorted('id'):
                identity = self._irg_tfm_resolve_grade_identity(
                    thesis.course_id,
                    thesis,
                )
                self._irg_tfm_validate_normalization(identity['line'], value)
                entries.append({
                    'identity': identity,
                    'old_points': thesis.points_fin,
                })

            self._irg_tfm_lock_identities([
                entry['identity'] for entry in entries
            ])
            for entry in entries:
                refreshed = self._irg_tfm_reresolve_after_locks(entry['identity'])
                self._irg_tfm_validate_normalization(refreshed['line'], value)
                entry['identity'] = refreshed
                entry['old_points'] = refreshed['thesis'].points_fin

            result = self.with_user(actor)._irg_tfm_write_business(dict(values))
            for entry in entries:
                refreshed = self._irg_tfm_reresolve_after_locks(
                    entry['identity']
                )
                self._irg_tfm_validate_normalization(refreshed['line'], value)
                entry['identity'] = refreshed
            sync_states = []
            for entry in entries:
                identity = entry['identity']
                result_state = self._irg_tfm_apply_forward_result(
                    identity,
                    value,
                    actor,
                )
                sync_states.append((identity, result_state))

            locked_enrollments = self.env['op.student.course'].sudo().browse(
                sorted({
                    entry['identity']['enrollment'].id for entry in entries
                })
            )
            self._irg_tfm_refresh_forward_changes(
                sync_states,
                locked_enrollments,
            )
            for entry, (_identity, result_state) in zip(entries, sync_states):
                thesis = entry['identity']['thesis']
                thesis.invalidate_recordset(['points_fin'])
                if thesis.points_fin != value:
                    raise ValidationError(_TFM_NORMALIZATION_ERROR)
                linked_result = result_state['result']
                if linked_result and linked_result.scoring_total != value:
                    raise ValidationError(_TFM_NORMALIZATION_ERROR)
                self._irg_tfm_audit_forward(
                    thesis,
                    actor,
                    entry['old_points'],
                    value,
                    result_state,
                )
            return result

    # ------------------------------------------------------------------
    # Reverse synchronization: app.gradebook.result -> tesis.model.points_fin
    # ------------------------------------------------------------------

    def _irg_tfm_resolve_reverse_identity(self, line):
        """Resolve enrollment, active thesis and full identity from a TFM line."""
        line = line.sudo().exists()
        line.ensure_one()
        admission = line.gradebook_student_id.admission_id
        if not admission:
            raise ValidationError(_TFM_GRADEBOOK_ERROR)
        enrollments = self.env['op.student.course'].sudo().search([
            ('student_id', '=', admission.student_id.id),
            ('course_id', '=', admission.course_id.id),
            ('batch_id', '=', admission.batch_id.id),
        ], order='id', limit=2)
        if len(enrollments) != 1:
            raise ValidationError(_TFM_ENROLLMENT_ERROR)
        subject = self._irg_tfm_resolve_subject_for_enrollment(enrollments)
        if subject != line.op_subject_id:
            raise ValidationError(_TFM_SUBJECT_ERROR)
        theses = self.sudo().search([
            ('course_id', '=', enrollments.id),
            ('irg_tfm_activated_at', '!=', False),
        ], order='id', limit=2)
        if len(theses) != 1:
            raise ValidationError(_TFM_THESIS_ERROR)
        identity = self._irg_tfm_resolve_grade_identity(enrollments, theses)
        if identity['line'] != line:
            raise ValidationError(_TFM_LINE_ERROR)
        return identity

    def _irg_tfm_reject_foreign_candidate(self, candidate, record=None):
        """A TFM candidate that is not this result is never linked silently."""
        if not candidate:
            return
        if record is not None and candidate.id == record.id:
            return
        raise ValidationError(
            _TFM_LINKED_EXAM_ERROR
            if candidate.irg_tfm_thesis_id else _TFM_EXAM_ERROR
        )

    def _irg_tfm_assert_reverse_pair(self, identity, state, value):
        """Both ends must hold exactly the requested score once hooks are done."""
        thesis = identity['thesis']
        thesis.invalidate_recordset(['points_fin'])
        if thesis.points_fin != value:
            raise ValidationError(_TFM_NORMALIZATION_ERROR)
        result = state['result']
        result.invalidate_recordset(['scoring_total'])
        if result.scoring_total != value:
            raise ValidationError(_TFM_NORMALIZATION_ERROR)
        return True

    def _irg_tfm_sync_gradebook_to_points(
        self,
        operation,
        actor,
        results,
        values,
        caller_context=None,
    ):
        """Private reverse coordinator; it is never reachable through RPC."""
        if operation == 'create':
            return self._irg_tfm_coordinate_reverse_create(
                results,
                values,
                actor,
                caller_context or {},
            )
        if operation == 'write':
            return self._irg_tfm_coordinate_reverse_write(results, values, actor)
        raise ValueError('Unsupported TFM grade operation: %s' % operation)

    def _irg_tfm_coordinate_reverse_create(self, results, values, actor, caller_context):
        with self.env.cr.savepoint():
            sync_savepoint = _TfmSyncSavepoint(self.env.cr)
            value = values.get('scoring_total', 0.0)
            self._irg_tfm_validate_score(value)
            try:
                line_id = int(values['gradebook_subject_id'])
            except (KeyError, TypeError, ValueError):
                raise ValidationError(_TFM_LINE_ERROR)
            line = self.env['app.gradebook.subject'].sudo().browse(line_id).exists()
            if not line:
                raise ValidationError(_TFM_LINE_ERROR)
            identity = self._irg_tfm_resolve_reverse_identity(line)
            self._irg_tfm_validate_normalization(identity['line'], value)
            self._irg_tfm_reject_foreign_candidate(identity['candidate'])

            self._irg_tfm_lock_identities([identity])
            identity = self._irg_tfm_reresolve_after_locks(identity)
            self._irg_tfm_validate_normalization(identity['line'], value)
            self._irg_tfm_reject_foreign_candidate(identity['candidate'])

            created = results._irg_tfm_create_business(values)
            identity = self._irg_tfm_reresolve_reverse_after_mutation(
                identity,
                new_results=created,
            )
            state = self._irg_tfm_apply_reverse_result(
                identity,
                created,
                value,
                actor,
                sync_savepoint,
            )
            self.env['app.gradebook.result'].sudo()._irg_tfm_refresh_affected_enrollments(
                identity['line'],
                locked_enrollments=identity['enrollment'],
            )
            self._irg_tfm_assert_reverse_pair(identity, state, value)
            self._irg_tfm_audit_reverse(identity['thesis'], actor, state, value)
            sync_savepoint.close()
            return results.with_context(caller_context).browse(created.ids)

    def _irg_tfm_coordinate_reverse_write(self, results, values, actor):
        with self.env.cr.savepoint():
            sync_savepoint = _TfmSyncSavepoint(self.env.cr)
            requested = values['scoring_total'] if 'scoring_total' in values else None
            previous_subjects = results.sudo()._irg_tfm_affected_subjects()
            entries = []
            for record in results.sudo().sorted('id'):
                line = record._irg_tfm_reverse_candidate_line(
                    values.get(
                        'gradebook_subject_id',
                        record.gradebook_subject_id.id,
                    ),
                    values.get('survey_type', record.survey_type),
                    linked=bool(record.irg_tfm_thesis_id),
                )
                if not line:
                    continue
                value = record.scoring_total if requested is None else requested
                self._irg_tfm_validate_score(value)
                identity = self._irg_tfm_resolve_reverse_identity(line)
                if (
                    record.gradebook_subject_id != identity['line']
                    or record.survey_type != 'exam'
                ):
                    raise ValidationError(_TFM_REVERSE_ADOPTION_ERROR)
                self._irg_tfm_validate_normalization(identity['line'], value)
                self._irg_tfm_reject_foreign_candidate(identity['candidate'], record)
                entries.append({
                    'record': record,
                    'identity': identity,
                    'value': value,
                    'previous_score': record.scoring_total,
                })
            if not entries:
                raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)

            self._irg_tfm_lock_identities([entry['identity'] for entry in entries])
            for entry in entries:
                identity = self._irg_tfm_reresolve_after_locks(entry['identity'])
                self._irg_tfm_validate_normalization(identity['line'], entry['value'])
                self._irg_tfm_reject_foreign_candidate(
                    identity['candidate'],
                    entry['record'],
                )
                if identity['candidate'].ids != entry['record'].ids:
                    raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
                entry['identity'] = identity
                entry['previous_score'] = identity['candidate'].scoring_total

            outcome = results._irg_tfm_write_business(values)

            states = []
            for entry in entries:
                identity = self._irg_tfm_reresolve_reverse_after_mutation(
                    entry['identity']
                )
                entry['identity'] = identity
                states.append((entry, self._irg_tfm_apply_reverse_result(
                    identity,
                    entry['record'],
                    entry['value'],
                    actor,
                    sync_savepoint,
                    previous_score=entry['previous_score'],
                )))

            synced_lines = self.env['app.gradebook.subject']
            locked_enrollments = self.env['op.student.course']
            for entry in entries:
                synced_lines |= entry['identity']['line']
                locked_enrollments |= entry['identity']['enrollment']
            self.env['app.gradebook.result'].sudo()._irg_tfm_refresh_affected_enrollments(
                synced_lines,
                locked_enrollments=locked_enrollments,
            )
            untouched = (
                previous_subjects | results.sudo()._irg_tfm_affected_subjects()
            ) - synced_lines
            if untouched:
                Result = self.env['app.gradebook.result'].sudo()
                Result._irg_tfm_refresh_affected_enrollments(untouched)
            for entry, state in states:
                self._irg_tfm_assert_reverse_pair(
                    entry['identity'],
                    state,
                    entry['value'],
                )
                self._irg_tfm_audit_reverse(
                    entry['identity']['thesis'],
                    actor,
                    state,
                    entry['value'],
                )
            sync_savepoint.close()
            return outcome

    def _irg_tfm_apply_reverse_result(
        self,
        identity,
        result,
        value,
        actor,
        sync_savepoint,
        previous_score=None,
    ):
        """Seal the verified link and mirror the gradebook grade onto the thesis.

        ``previous_score`` is the gradebook value before this operation, which
        the coordinator captured under lock; ``None`` means the row did not
        exist yet, exactly like the forward audit.
        """
        thesis = identity['thesis']
        thesis.ensure_one()
        Result = self.env['app.gradebook.result'].sudo()
        result = Result.browse(result.id).exists()
        if not result:
            raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
        old_points = thesis.points_fin
        old_result_score = previous_score
        link_changed = False
        if not result.irg_tfm_thesis_id:
            result._irg_tfm_internal_write({'irg_tfm_thesis_id': thesis.id})
            link_changed = True
        result.invalidate_recordset([
            'gradebook_subject_id', 'survey_type', 'scoring_total',
            'irg_tfm_thesis_id',
        ])
        result = Result.browse(result.id).exists()
        if not result or (
            result.irg_tfm_thesis_id != thesis
            or result.gradebook_subject_id != identity['line']
            or result.survey_type != 'exam'
        ):
            raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
        if result.scoring_total != value:
            raise ValidationError(_TFM_NORMALIZATION_ERROR)
        thesis._irg_tfm_apply_inverse_from_verified_gradebook(
            actor=actor,
            verified_link=result,
            value=result.scoring_total,
            sync_savepoint=sync_savepoint,
        )
        return {
            'result': result,
            'old_points': old_points,
            'old_result_score': old_result_score,
            'link_changed': link_changed,
        }

    def _irg_tfm_apply_inverse_from_verified_gradebook(
        self,
        actor,
        verified_link,
        value,
        sync_savepoint,
    ):
        """Write only ``points_fin`` from a link the coordinator already verified.

        The already-authorized actor and the already-verified link arrive
        explicitly, and the savepoint object proves the private caller: RPC
        payloads are JSON, so no client can build one.  The elevated write is
        scoped to this record and this field, never reaches the public thesis
        boundary and accepts no context marker.
        """
        if not isinstance(sync_savepoint, _TfmSyncSavepoint):
            raise AccessError(_TFM_SAVEPOINT_ERROR)
        sync_savepoint.assert_open(self.env.cr)
        self.ensure_one()
        if not actor or actor._name != 'res.users' or len(actor) != 1:
            raise AccessError(_TFM_SAVEPOINT_ERROR)
        verified_link.ensure_one()
        verified_link = verified_link.sudo().exists()
        if not verified_link or verified_link.survey_type != 'exam':
            raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
        if verified_link.irg_tfm_thesis_id != self:
            raise ValidationError(_TFM_CONCURRENT_MAPPING_ERROR)
        self._irg_tfm_validate_score(value)
        if verified_link.scoring_total != value:
            raise ValidationError(_TFM_NORMALIZATION_ERROR)
        thesis = self.sudo()
        if thesis.points_fin != value:
            thesis._irg_tfm_write_business({'points_fin': value})
        thesis.invalidate_recordset(['points_fin'])
        if thesis.points_fin != value:
            raise ValidationError(_TFM_NORMALIZATION_ERROR)
        return True

    def _irg_tfm_audit_reverse(self, thesis, actor, state, value):
        result = state['result']
        effective_change = (
            state['old_points'] != value
            or state['old_result_score'] != value
            or state['link_changed']
        )
        if not effective_change:
            return
        actor_label = str(escape(actor.display_name))
        result_label = str(escape(result.display_name or ''))
        old_result = state['old_result_score']
        old_result_label = (
            'sin resultado' if old_result is None else str(old_result)
        )
        body = _(
            'Sincronización de nota TFM: actor=%(actor)s (uid=%(uid)s); '
            'origen=gradebook; tesis=%(old_thesis)s→%(new)s; '
            'libreta=%(old_result)s→%(new)s; nuevo=%(new)s; '
            'resultado=%(result_id)s (%(result)s).'
        ) % {
            'actor': actor_label,
            'uid': actor.id,
            'old_thesis': state['old_points'],
            'old_result': old_result_label,
            'new': value,
            'result_id': result.id,
            'result': result_label,
        }
        # The mirror needs elevation, so the original actor is preserved both as
        # the message author and inside the audited body.
        thesis.sudo().message_post(body=body, author_id=actor.partner_id.id)

    # ------------------------------------------------------------------
    # Server-side protection of a linked result and its identity parents
    # ------------------------------------------------------------------

    def _irg_tfm_link_guard_scope(self, records):
        """Collect every row of the TFM link graph reachable from ``records``."""
        Enrollment = self.env['op.student.course'].sudo()
        Admission = self.env['op.admission'].sudo()
        Gradebook = self.env['app.gradebook.student'].sudo()
        Line = self.env['app.gradebook.subject'].sudo()
        Result = self.env['app.gradebook.result'].sudo()
        enrollments = Enrollment.browse()
        admissions = Admission.browse()
        theses = self.sudo().browse()
        gradebooks = Gradebook.browse()
        lines = Line.browse()
        results = Result.browse()

        model = records._name
        if model == 'app.gradebook.result':
            results = Result.browse(records.ids).exists()
        elif model == 'app.gradebook.subject':
            lines = Line.browse(records.ids).exists()
        elif model == 'app.gradebook.student':
            gradebooks = Gradebook.browse(records.ids).exists()
        elif model == 'op.admission':
            admissions = Admission.browse(records.ids).exists()
        elif model == 'op.student.course':
            enrollments = Enrollment.browse(records.ids).exists()
        elif model == 'tesis.model':
            theses = self.sudo().browse(records.ids).exists()
        else:
            raise ValueError('Unsupported TFM link guard model: %s' % model)

        if enrollments:
            theses |= self.sudo().search([
                ('course_id', 'in', enrollments.ids),
            ], order='id')
            pairs = {
                (
                    enrollment.student_id.id,
                    enrollment.course_id.id,
                    enrollment.batch_id.id,
                )
                for enrollment in enrollments
                if enrollment.student_id
                and enrollment.course_id
                and enrollment.batch_id
            }
            if pairs:
                admissions |= Admission.search([
                    ('student_id', 'in', [pair[0] for pair in pairs]),
                    ('course_id', 'in', [pair[1] for pair in pairs]),
                    ('batch_id', 'in', [pair[2] for pair in pairs]),
                ], order='id').filtered(
                    lambda admission: (
                        admission.student_id.id,
                        admission.course_id.id,
                        admission.batch_id.id,
                    ) in pairs
                )
        if admissions:
            gradebooks |= Gradebook.search([
                ('admission_id', 'in', admissions.ids),
            ], order='id')
        if gradebooks:
            lines |= Line.search([
                ('gradebook_student_id', 'in', gradebooks.ids),
            ], order='id')
        if lines:
            results |= Result.search([
                ('gradebook_subject_id', 'in', lines.ids),
            ], order='id')
        if theses:
            results |= Result.search([
                ('irg_tfm_thesis_id', 'in', theses.ids),
            ], order='id')

        results = results.exists()
        lines = (lines | results.gradebook_subject_id).exists()
        gradebooks = (gradebooks | lines.gradebook_student_id).exists()
        admissions = (admissions | gradebooks.admission_id).exists()
        theses = (theses | results.irg_tfm_thesis_id).exists()
        enrollments |= theses.course_id
        for admission in admissions:
            enrollments |= Enrollment.search([
                ('student_id', '=', admission.student_id.id),
                ('course_id', '=', admission.course_id.id),
                ('batch_id', '=', admission.batch_id.id),
            ], order='id')
        return {
            'op_student_course': enrollments.exists().ids,
            'op_admission': admissions.ids,
            'tesis_model': theses.ids,
            'app_gradebook_student': gradebooks.ids,
            'app_gradebook_subject': lines.ids,
            'app_gradebook_result': results.ids,
            'linked_results': results.filtered(
                lambda result: result.irg_tfm_thesis_id
            ),
        }

    def _irg_tfm_assert_no_linked_identity(self, records):
        """Lock the whole hierarchy first, then reread before rejecting."""
        scope = self._irg_tfm_link_guard_scope(records)
        for table in _TFM_LINK_GUARD_LOCK_PHASES:
            self._irg_tfm_lock_rows(table, scope[table])
        self._irg_tfm_invalidate_identity()
        refreshed = self._irg_tfm_link_guard_scope(records)
        if refreshed['linked_results']:
            raise AccessError(_TFM_LINKED_IDENTITY_ERROR)
        return True

    def _irg_tfm_guard_linked_identity(self, records, operation):
        """Authorize the actor first; only then read the link with elevation."""
        records = records.exists()
        if not records:
            return True
        records.check_access_rights(operation)
        records.check_access_rule(operation)
        return self._irg_tfm_assert_no_linked_identity(records)
