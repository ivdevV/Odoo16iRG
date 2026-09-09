from markupsafe import escape

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, ValidationError


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
        return any(
            submission._irg_is_tfm_outline_submission()
            for submission in self.irg_tfm_submission_ids
        )

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
        if any(vals.get('irg_tfm_convocation_id') for vals in vals_list):
            raise ValidationError(
                _('Create the thesis first, then assign its TFM convocation.'),
            )
        return super().create(vals_list)

    def _send_email_notification(self):
        if self.env.context.get('irg_tfm_auto_activation'):
            return True
        return super()._send_email_notification()

    def write(self, vals):
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
