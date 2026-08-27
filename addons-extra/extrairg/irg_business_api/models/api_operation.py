# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools.translate import _

from .api_constants import (
    ALLOWED_ENVIRONMENTS,
    MAX_PAYLOAD_BYTES,
    OPERATION_CODES,
    OPERATION_SPECS,
)
from . import api_serializer as ser
from .academic_service import AcademicService
from .elearning_service import ElearningService
from .access_service import AccessService
from .gradebook_service import GradebookService
from .moodle_service import MoodleService

_logger = logging.getLogger(__name__)

SERVER_OWNED_FIELDS = {
    'request_hash', 'state', 'before_snapshot', 'proposed_after',
    'result_snapshot', 'changed_fields', 'warnings', 'errors',
    'requested_by', 'approved_by', 'applied_by', 'approved_at',
    'applied_at', 'verified_at', 'audit_reference', 'company_id',
}


class IrgApiOperation(models.Model):
    _name = 'irg.api.operation'
    _description = 'IRG Business API Operation'
    _order = 'id desc'
    _rec_name = 'operation_code'

    operation_code = fields.Selection(OPERATION_CODES, required=True, index=True)
    environment = fields.Selection([
        ('test', 'Test'),
        ('beta', 'Beta'),
        ('production', 'Production'),
    ], required=True, default='test', index=True)
    target_model = fields.Char(readonly=True)
    target_id = fields.Integer(readonly=True)
    request_payload = fields.Text(required=True)
    request_hash = fields.Char(readonly=True, index=True)
    idempotency_key = fields.Char(required=True, index=True)
    state = fields.Selection([
        ('preview', 'Preview'),
        ('awaiting_approval', 'Awaiting Approval'),
        ('applied', 'Applied'),
        ('rejected', 'Rejected'),
        ('failed', 'Failed'),
        ('verified', 'Verified'),
    ], default='preview', required=True, readonly=True, index=True)
    before_snapshot = fields.Text(readonly=True)
    proposed_after = fields.Text(readonly=True)
    result_snapshot = fields.Text(readonly=True)
    changed_fields = fields.Text(readonly=True)
    warnings = fields.Text(readonly=True)
    errors = fields.Text(readonly=True)
    requested_by = fields.Many2one('res.users', readonly=True, required=True, index=True)
    approved_by = fields.Many2one('res.users', readonly=True)
    applied_by = fields.Many2one('res.users', readonly=True)
    approved_at = fields.Datetime(readonly=True)
    applied_at = fields.Datetime(readonly=True)
    verified_at = fields.Datetime(readonly=True)
    audit_reference = fields.Char(readonly=True)
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company.id,
        index=True,
    )

    _sql_constraints = [
        (
            'idempotency_uniq',
            'unique(requested_by, operation_code, idempotency_key)',
            'This idempotency key was already used for this operation.',
        ),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        self._irg_check_actor()
        records = self.browse()
        for vals in vals_list:
            records |= self._irg_create_one(dict(vals))
        return records

    def write(self, vals):
        raise AccessError(_('API operation fields cannot be written directly.'))

    def unlink(self):
        raise AccessError(_('API operations cannot be deleted.'))

    def action_approve(self):
        self.ensure_one()
        self._irg_check_actor()
        self._irg_assert_owner()
        return self._irg_apply_preview()

    def action_reject(self):
        self.ensure_one()
        self._irg_check_actor()
        self._irg_assert_owner()
        if self.state not in ('preview', 'awaiting_approval'):
            raise UserError(_('Only previewed operations can be rejected.'))
        self._irg_internal_write({
            'state': 'rejected',
            'approved_by': self.env.uid,
            'approved_at': fields.Datetime.now(),
        })
        return True

    def _irg_create_one(self, vals):
        for key in list(vals):
            if key in SERVER_OWNED_FIELDS:
                vals.pop(key)
        code = vals.get('operation_code')
        spec = OPERATION_SPECS.get(code)
        if not spec:
            raise UserError(_('Unknown or unpublished operation.'))
        environment = vals.get('environment') or 'test'
        if environment not in ALLOWED_ENVIRONMENTS:
            raise UserError(_('Environment %s is not allowed.') % environment)
        raw_payload = vals.get('request_payload') or '{}'
        if isinstance(raw_payload, dict):
            raw_payload = ser.canonical_dumps(raw_payload)
        if not isinstance(raw_payload, str):
            raise UserError(_('request_payload must be JSON text.'))
        if len(raw_payload.encode('utf-8')) > MAX_PAYLOAD_BYTES:
            raise UserError(_('Payload exceeds %s bytes.') % MAX_PAYLOAD_BYTES)
        payload = ser.parse_payload(raw_payload)
        unknown = set(payload) - spec['keys']
        if unknown:
            raise UserError(_('Unsupported payload keys: %s') % ', '.join(sorted(unknown)))
        payload = ser.sanitize_mapping(payload)
        digest = ser.payload_hash(payload)
        key = (vals.get('idempotency_key') or '').strip()
        if not key:
            raise UserError(_('idempotency_key is required.'))
        existing = self.search([
            ('requested_by', '=', self.env.uid),
            ('operation_code', '=', code),
            ('idempotency_key', '=', key),
        ], limit=1)
        if existing:
            if existing.request_hash != digest:
                raise UserError(_('This idempotency key was used with a different payload.'))
            return existing
        vals.update({
            'environment': environment,
            'request_payload': ser.canonical_dumps(payload),
            'request_hash': digest,
            'requested_by': self.env.uid,
            'company_id': self.env.company.id,
            'state': 'preview',
            'idempotency_key': key,
        })
        record = super().create(vals)
        record._irg_internal_write({
            'audit_reference': 'IRGAPI/%s' % record.id,
        })
        try:
            record._irg_dispatch(payload, spec)
        except Exception as err:
            record._irg_internal_write({
                'state': 'failed',
                'errors': ser.dumps_public({'error': str(err)}),
            })
            raise
        return record

    def _irg_dispatch(self, payload=None, spec=None):
        self.ensure_one()
        self._irg_check_actor()
        spec = spec or OPERATION_SPECS.get(self.operation_code)
        if not spec:
            raise UserError(_('Unknown or unpublished operation.'))
        payload = payload if payload is not None else ser.parse_payload(self.request_payload)
        kind = spec['kind']
        # sudo: facade users have no ACL on academic models; group+allowlist already checked.
        academic_env = self.sudo().env
        if kind == 'read':
            result = self._irg_run_read(academic_env, payload)
            self._irg_internal_write({
                'state': 'verified',
                'result_snapshot': ser.dumps_public(ser.sanitize_mapping(result)),
                'verified_at': fields.Datetime.now(),
                'applied_by': self.env.uid,
                'applied_at': fields.Datetime.now(),
            })
            return True
        if kind == 'meta':
            return self._irg_run_meta(payload)
        before, proposed, target = self._irg_run_preview(academic_env, payload)
        self._irg_internal_write({
            'state': 'preview',
            'before_snapshot': ser.dumps_public(ser.sanitize_mapping(before)),
            'proposed_after': ser.dumps_public(ser.sanitize_mapping(proposed)),
            'target_model': target.get('model'),
            'target_id': target.get('id') or 0,
            'changed_fields': ser.dumps_public(sorted(
                set(proposed) - set(before) or [
                    key for key in proposed if proposed.get(key) != before.get(key)
                ]
            )),
        })
        return True

    def _irg_run_read(self, env, payload):
        academic = AcademicService(env)
        elearning = ElearningService(env)
        access = AccessService(env)
        gradebook = GradebookService(env)
        moodle = MoodleService(env)
        code = self.operation_code
        dispatch = {
            'irg_list_academic_periods': academic.list_academic_periods,
            'irg_list_courses': academic.list_courses,
            'irg_get_course_overview': academic.get_course_overview,
            'irg_get_course_batches': academic.get_course_batches,
            'irg_list_subjects': academic.list_subjects,
            'irg_get_course_structure': elearning.get_course_structure,
            'irg_get_slide': elearning.get_slide,
            'irg_get_admission_overview': academic.get_admission_overview,
            'irg_get_admission_subject_openings': academic.get_admission_subject_openings,
            'irg_get_student_access': access.get_student_access,
            'irg_get_student_academic_360': access.get_student_academic_360,
            'irg_get_gradebook_summary': gradebook.get_gradebook_summary,
            'irg_get_moodle_sync_status': moodle.get_moodle_sync_status,
            'irg_get_survey_structure': academic.get_survey_structure,
            'irg_get_academic_incidents': access.get_academic_incidents,
        }
        handler = dispatch.get(code)
        if not handler:
            raise UserError(_('Read operation is not implemented.'))
        return handler(payload)

    def _irg_run_preview(self, env, payload):
        elearning = ElearningService(env)
        code = self.operation_code
        if code == 'irg_create_slide_draft':
            return elearning.preview_create_slide(payload)
        if code == 'irg_update_slide_draft':
            return elearning.preview_update_slide(payload)
        if code == 'irg_create_course_section':
            return elearning.preview_create_section(payload)
        if code == 'irg_reorder_course_section':
            return elearning.preview_reorder_sections(payload)
        if code == 'irg_publish_slide':
            return elearning.preview_publish(payload, publish=True)
        if code == 'irg_unpublish_slide':
            return elearning.preview_publish(payload, publish=False)
        raise UserError(_('Write operation is not implemented.'))

    def _irg_run_meta(self, payload):
        target_id = ser.require_positive_id(payload, 'operation_id')
        target = self.search([
            ('id', '=', target_id),
            ('requested_by', '=', self.env.uid),
        ], limit=1)
        if not target and self.env.user.has_group('base.group_system'):
            target = self.browse(target_id).exists()
        if not target:
            raise UserError(_('Operation %s was not found.') % target_id)
        if self.operation_code == 'irg_approve_operation':
            target._irg_apply_preview()
            self._irg_internal_write({
                'state': 'verified',
                'target_model': 'irg.api.operation',
                'target_id': target.id,
                'result_snapshot': ser.dumps_public({'approved_operation_id': target.id, 'state': target.state}),
                'verified_at': fields.Datetime.now(),
                'applied_by': self.env.uid,
                'applied_at': fields.Datetime.now(),
            })
            return True
        target.action_reject()
        self._irg_internal_write({
            'state': 'verified',
            'target_model': 'irg.api.operation',
            'target_id': target.id,
            'result_snapshot': ser.dumps_public({'rejected_operation_id': target.id}),
            'verified_at': fields.Datetime.now(),
            'applied_by': self.env.uid,
            'applied_at': fields.Datetime.now(),
        })
        return True

    def _irg_apply_preview(self):
        self.ensure_one()
        self._irg_check_actor()
        self._irg_assert_owner()
        self.env.cr.execute(
            'SELECT id FROM irg_api_operation WHERE id = %s FOR UPDATE',
            [self.id],
        )
        self.invalidate_recordset(['state'])
        if self.state in ('applied', 'verified'):
            return True
        if self.state not in ('preview', 'awaiting_approval'):
            raise UserError(_('Operation %s cannot be approved from state %s.') % (
                self.operation_code, self.state,
            ))
        payload = ser.parse_payload(self.request_payload)
        before = ser.parse_payload(self.before_snapshot)
        proposed = ser.parse_payload(self.proposed_after)
        # sudo: apply uses the same authorized academic path as preview.
        env = self.sudo().env
        elearning = ElearningService(env)
        cr = self.env.cr
        cr.execute('SAVEPOINT irg_api_apply')
        try:
            if self.operation_code == 'irg_create_slide_draft':
                result = elearning.apply_create_slide(proposed)
                elearning.verify_create_slide(result)
            elif self.operation_code == 'irg_update_slide_draft':
                result = elearning.apply_update_slide(proposed, before)
            elif self.operation_code == 'irg_create_course_section':
                result = elearning.apply_create_section(proposed)
            elif self.operation_code == 'irg_reorder_course_section':
                result = elearning.apply_reorder_sections(proposed, before)
            elif self.operation_code in ('irg_publish_slide', 'irg_unpublish_slide'):
                result = elearning.apply_publish(proposed, before)
            else:
                raise UserError(_('This operation cannot be applied.'))
            cr.execute('RELEASE SAVEPOINT irg_api_apply')
        except Exception:
            cr.execute('ROLLBACK TO SAVEPOINT irg_api_apply')
            self._irg_internal_write({
                'state': 'failed',
                'errors': ser.dumps_public({'error': 'apply_failed'}),
            })
            raise
        now = fields.Datetime.now()
        self._irg_internal_write({
            'state': 'verified',
            'result_snapshot': ser.dumps_public(ser.sanitize_mapping(result)),
            'target_id': result.get('id') or self.target_id,
            'approved_by': self.env.uid,
            'applied_by': self.env.uid,
            'approved_at': now,
            'applied_at': now,
            'verified_at': now,
        })
        return True

    def _irg_internal_write(self, vals):
        return super(IrgApiOperation, self).write(vals)

    def _irg_check_actor(self):
        if self.env.su:
            return True
        user = self.env.user
        if user.has_group('irg_business_api.group_irg_business_api_user'):
            return True
        if user.has_group('base.group_system'):
            return True
        raise AccessError(_('You cannot run IRG business API operations.'))

    def _irg_assert_owner(self):
        if self.env.su or self.env.user.has_group('base.group_system'):
            return True
        if self.requested_by != self.env.user:
            raise AccessError(_('You cannot approve another user\'s operation.'))
        return True
