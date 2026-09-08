# -*- coding: utf-8 -*-
import base64
import hashlib
import re

from odoo import fields
from odoo.exceptions import UserError
from odoo.tools.translate import _

from . import api_serializer as ser

DIPLOMA_TYPES = {'digital', 'physical'}
CERTIFICATE_TYPES = {'digital', 'physical', 'custom', 'physical_apostilled'}
PHYSICAL_TYPES = {'physical', 'physical_apostilled'}
SIGNERS = {'dpto_academico', 'raimon'}
SHIPPING_TYPES = {'national', 'international'}
CUSTOM_OPTIONS = {'language_en', 'language_fr', 'specific_subjects', 'official_seal'}
CONTENT_ID_RE = re.compile(r'/web/content/(\d+)')


class AcademicDocumentService:

    def __init__(self, env):
        self.env = env

    def _browse(self, model_name, key, payload):
        record = self.env[model_name].browse(ser.require_positive_id(payload, key))
        if not record.exists():
            raise UserError(_('Unknown %s.') % key)
        return record

    def _pdf_from_action(self, action):
        url = (action or {}).get('url') or ''
        match = CONTENT_ID_RE.search(url)
        if not match:
            raise UserError(_('PDF was not generated.'))
        attachment = self.env['ir.attachment'].with_context(bin_size=False).browse(
            int(match.group(1))
        )
        if not attachment.exists():
            raise UserError(_('PDF was not generated.'))
        if 'public' in attachment._fields and attachment.public:
            raise UserError(_('PDF must remain private.'))
        raw = base64.b64decode(attachment.datas or b'')
        if not raw:
            raise UserError(_('PDF was not generated.'))
        checksum = hashlib.sha256(raw).hexdigest()
        file_b64 = attachment.datas
        if isinstance(file_b64, bytes):
            file_b64 = file_b64.decode('ascii')
        return attachment, checksum, file_b64

    def _word_options(self, payload):
        certificate_type = (payload.get('certificate_type') or '').strip()
        if certificate_type not in CERTIFICATE_TYPES:
            raise UserError(_('certificate_type is not valid.'))
        signer = (payload.get('signer') or '').strip()
        if signer not in SIGNERS:
            raise UserError(_('signer is required and must be dpto_academico or raimon.'))
        shipping_type = (payload.get('shipping_type') or '').strip() or False
        if certificate_type in PHYSICAL_TYPES:
            if shipping_type not in SHIPPING_TYPES:
                raise UserError(_('shipping_type is required for physical certificates.'))
        elif shipping_type:
            raise UserError(_('shipping_type is only allowed for physical certificates.'))
        custom_options = payload.get('custom_options') or False
        if custom_options and custom_options not in CUSTOM_OPTIONS:
            raise UserError(_('custom_options is not valid.'))
        options = {
            'certificate_type': certificate_type,
            'signer': signer,
            'shipping_type': shipping_type,
        }
        if payload.get('custom_description'):
            options['custom_description'] = payload['custom_description']
        if custom_options:
            options['custom_options'] = custom_options
        return options

    def _admission(self, payload):
        if 'op.admission' not in self.env:
            raise UserError(_('Admissions are not installed.'))
        return self._browse('op.admission', 'admission_id', payload)

    def _enrolment_record_for_admission(self, admission):
        if 'app.gradebook.student' not in self.env or 'irg.certificate.request' not in self.env:
            raise UserError(_('Enrolment certificates are not installed.'))
        Gradebook = self.env['app.gradebook.student']
        records = Gradebook.search([('admission_id', '=', admission.id)])
        if not records:
            raise UserError(_('No academic enrolment record was found for this admission.'))
        if admission.batch_id:
            matched = records.filtered(lambda rec: rec.batch_id.id == admission.batch_id.id)
            if matched:
                if len(matched) > 1:
                    raise UserError(_(
                        'Multiple academic enrolment records were found for this admission and group.'
                    ))
                return matched
        if len(records) > 1:
            raise UserError(_(
                'Multiple academic enrolment records were found for this admission.'
            ))
        return records

    def _issue_word_certificate(self, admission, document_type, options, session=None):
        record = self._enrolment_record_for_admission(admission)
        vals = {
            'gradebook_student_id': record.id,
            'document_type': document_type,
            'state': 'done',
            'origin': 'backend',
        }
        vals.update(options)
        if session:
            vals['session_id'] = session.id
        cert = self.env['irg.certificate.request'].create(vals)
        cert._generate_and_attach_pdf()
        return cert.action_download_pdf()

    def _word_result(self, action):
        attachment, checksum, file_b64 = self._pdf_from_action(action)
        if attachment.res_model != 'irg.certificate.request':
            raise UserError(_('PDF was not generated.'))
        cert = self.env['irg.certificate.request'].browse(attachment.res_id)
        if not cert.exists():
            raise UserError(_('PDF was not generated.'))
        return {
            'certificate_request_id': cert.id,
            'name': cert.name,
            'state': cert.state,
            'attachment_id': attachment.id,
            'attachment_name': attachment.name,
            'mimetype': attachment.mimetype or 'application/pdf',
            'checksum': checksum,
            'file_b64': file_b64,
            'public': False,
        }

    def _proposed_word(self, admission, options, extra=None):
        proposed = {
            'admission_id': admission.id,
            'certificate_type': options['certificate_type'],
            'signer': options['signer'],
            'shipping_type': options.get('shipping_type') or False,
            'will_call': 'irg.certificate.request._generate_and_attach_pdf',
        }
        if options.get('custom_description'):
            proposed['custom_description'] = options['custom_description']
        if options.get('custom_options'):
            proposed['custom_options'] = options['custom_options']
        if extra:
            proposed.update(extra)
        return proposed

    def _payload_from_word_proposed(self, proposed):
        payload = {
            'admission_id': proposed.get('admission_id'),
            'certificate_type': proposed.get('certificate_type'),
            'signer': proposed.get('signer'),
            'shipping_type': proposed.get('shipping_type') or False,
        }
        if proposed.get('custom_description'):
            payload['custom_description'] = proposed['custom_description']
        if proposed.get('custom_options'):
            payload['custom_options'] = proposed['custom_options']
        if proposed.get('session_id'):
            payload['session_id'] = proposed['session_id']
        return payload

    def preview_generate_enrollment(self, payload):
        admission = self._admission(payload)
        options = self._word_options(payload)
        self._enrolment_record_for_admission(admission)
        before = {
            'admission_id': admission.id,
            'admission_state': admission.state,
        }
        proposed = self._proposed_word(admission, options)
        return before, proposed, {'model': 'op.admission', 'id': admission.id}

    def apply_generate_enrollment(self, proposed, before):
        payload = self._payload_from_word_proposed(proposed)
        admission = self._admission(payload)
        if admission.id != before.get('admission_id'):
            raise UserError(_('The admission changed after preview.'))
        if admission.state != before.get('admission_state'):
            raise UserError(_('The admission changed after preview.'))
        options = self._word_options(payload)
        action = self._issue_word_certificate(admission, 'enrollment', options)
        return self._word_result(action)

    def preview_generate_attendance(self, payload):
        if (
            'irg.certificate.request' not in self.env
            or 'session_id' not in self.env['irg.certificate.request']._fields
        ):
            raise UserError(_('Attendance certificates are not installed.'))
        admission = self._admission(payload)
        options = self._word_options(payload)
        if not payload.get('session_id'):
            raise UserError(_('session_id is required for attendance certificates.'))
        session = self._browse('op.session', 'session_id', payload)
        if admission.batch_id and session.batch_id and session.batch_id.id != admission.batch_id.id:
            raise UserError(_('session_id does not belong to this admission.'))
        record = self._enrolment_record_for_admission(admission)
        rec = self.env['irg.certificate.request'].new({
            'gradebook_student_id': record.id,
            'document_type': 'attendance',
            'session_id': session.id,
            **options,
        })
        rec._validate_attendance_request()
        before = {
            'admission_id': admission.id,
            'admission_state': admission.state,
        }
        proposed = self._proposed_word(admission, options, extra={'session_id': session.id})
        return before, proposed, {'model': 'op.admission', 'id': admission.id}

    def apply_generate_attendance(self, proposed, before):
        payload = self._payload_from_word_proposed(proposed)
        if (
            'irg.certificate.request' not in self.env
            or 'session_id' not in self.env['irg.certificate.request']._fields
        ):
            raise UserError(_('Attendance certificates are not installed.'))
        admission = self._admission(payload)
        if admission.id != before.get('admission_id'):
            raise UserError(_('The admission changed after preview.'))
        if admission.state != before.get('admission_state'):
            raise UserError(_('The admission changed after preview.'))
        options = self._word_options(payload)
        if not payload.get('session_id'):
            raise UserError(_('session_id is required for attendance certificates.'))
        session = self._browse('op.session', 'session_id', payload)
        if admission.batch_id and session.batch_id and session.batch_id.id != admission.batch_id.id:
            raise UserError(_('session_id does not belong to this admission.'))
        record = self._enrolment_record_for_admission(admission)
        rec = self.env['irg.certificate.request'].new({
            'gradebook_student_id': record.id,
            'document_type': 'attendance',
            'session_id': session.id,
            **options,
        })
        rec._validate_attendance_request()
        action = self._issue_word_certificate(
            admission, 'attendance', options, session=session,
        )
        return self._word_result(action)

    def _diploma_vals(self, payload):
        if 'irg.diploma.wizard' not in self.env:
            raise UserError(_('Diploma generation is not installed.'))
        student = self._browse('op.student', 'student_id', payload)
        course = self._browse('op.student.course', 'student_course_id', payload)
        if course.student_id.id != student.id:
            raise UserError(_('student_course_id does not belong to student_id.'))
        if 'state' in course._fields and course.state != 'finished':
            raise UserError(_(
                'student_course_id must be a finished course to generate a diploma.'
            ))
        diploma_type = (payload.get('diploma_type') or '').strip()
        if diploma_type not in DIPLOMA_TYPES:
            raise UserError(_('diploma_type must be digital or physical.'))
        vals = {
            'student_id': student.id,
            'student_course_id': course.id,
            'diploma_type': diploma_type,
        }
        if payload.get('issue_date'):
            try:
                vals['date'] = fields.Date.to_date(payload['issue_date'])
            except (TypeError, ValueError):
                raise UserError(_('issue_date must be a date (YYYY-MM-DD).'))
        return student, course, vals

    def preview_generate_diploma(self, payload):
        student, course, vals = self._diploma_vals(payload)
        self.env['irg.diploma.wizard'].create(vals)
        proposed = {
            'student_id': student.id,
            'student_course_id': course.id,
            'diploma_type': vals['diploma_type'],
            'course_state': course.state,
            'will_call': 'irg.diploma.wizard.action_print_diploma',
            'will_create': 'irg.diploma.registry',
        }
        if vals.get('date'):
            proposed['issue_date'] = fields.Date.to_string(vals['date'])
        before = {
            'student_id': student.id,
            'student_course_id': course.id,
            'course_state': course.state,
        }
        return before, proposed, {'model': 'op.student', 'id': student.id}

    def apply_generate_diploma(self, proposed, before):
        payload = {
            'student_id': proposed.get('student_id'),
            'student_course_id': proposed.get('student_course_id'),
            'diploma_type': proposed.get('diploma_type'),
        }
        if proposed.get('issue_date'):
            payload['issue_date'] = proposed['issue_date']
        student, course, vals = self._diploma_vals(payload)
        if (
            student.id != before.get('student_id')
            or course.id != before.get('student_course_id')
            or course.state != before.get('course_state')
        ):
            raise UserError(_('The student course changed after preview.'))
        wizard = self.env['irg.diploma.wizard'].create(vals)
        action = wizard.action_print_diploma()
        attachment, checksum, file_b64 = self._pdf_from_action(action)
        result = {
            'attachment_id': attachment.id,
            'attachment_name': attachment.name,
            'mimetype': attachment.mimetype or 'application/pdf',
            'checksum': checksum,
            'file_b64': file_b64,
            'public': False,
        }
        if 'irg.diploma.registry' in self.env:
            registry = self.env['irg.diploma.registry'].search([
                ('attachment_id', '=', attachment.id),
            ], limit=1)
            if registry:
                result['diploma_registry_id'] = registry.id
                result['registry_number'] = registry.registry_number
                result['state'] = registry.state
        return result
