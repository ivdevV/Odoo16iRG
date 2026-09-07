# -*- coding: utf-8 -*-
import base64
import hashlib
from contextlib import ExitStack
from datetime import date
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import IrgBusinessApiCase

PDF_BYTES = (
    b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
    b'1 0 obj<</Type/Catalog>>endobj\n'
    b'trailer<>\n%%EOF\n'
)
PDF_CHECKSUM = hashlib.sha256(PDF_BYTES).hexdigest()


@tagged('post_install', '-at_install', 'irg_business_api')
class TestGradebookCertificateOperation(IrgBusinessApiCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if 'app.gradebook.student' not in cls.env or 'irg.certificate.wizard' not in cls.env:
            cls._certs_available = False
            return
        cls._certs_available = True
        tmpl_vals = {'name': 'API Cert Template'}
        GradebookTmpl = cls.env['app.gradebook']
        if 'gradebook_template_ids' in GradebookTmpl._fields:
            tmpl_vals['gradebook_template_ids'] = [(0, 0, {
                'type': 'exam',
                'qty': 1,
                'weight': 100,
            })]
        cls.gradebook_tmpl = GradebookTmpl.create(tmpl_vals)
        if 'gradebook_id' in cls.course._fields:
            cls.course.write({'gradebook_id': cls.gradebook_tmpl.id})
        cls.gradebook = cls.env['app.gradebook.student'].create({
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'admission_id': cls.admission.id,
        })
        if 'op.subject' in cls.env:
            subject = cls.subject
            cls.gb_subject = cls.env['app.gradebook.subject'].create({
                'gradebook_student_id': cls.gradebook.id,
                'op_subject_id': subject.id,
            })
            if 'app.gradebook.result' in cls.env:
                cls.env['app.gradebook.result'].create({
                    'gradebook_subject_id': cls.gb_subject.id,
                    'survey_type': 'exam',
                    'scoring_total': 8.0,
                })
                if hasattr(cls.gb_subject, 'compute_final_subject_note'):
                    cls.gb_subject.compute_final_subject_note()
        cls._attendance_available = (
            'session_id' in cls.env['irg.certificate.request']._fields
            and 'op.session' in cls.env
            and 'op.faculty' in cls.env
        )
        cls.hc_gradebook = False
        cls.hc_session = False
        if cls._attendance_available:
            hc_batch = cls.env['op.batch'].create({
                'name': 'API Batch HC',
                'code': 'APIHC%s' % cls.batch.code[-4:],
                'course_id': cls.course.id,
                'start_date': date(2026, 1, 1),
                'end_date': date(2026, 12, 31),
            })
            hc_admission = cls.env['op.admission'].create({
                'first_name': 'API',
                'last_name': 'HC',
                'name': 'API HC Student',
                'birth_date': date(1990, 1, 1),
                'gender': 'o',
                'email': 'api.hc.student@example.com',
                'register_id': cls.register.id,
                'course_id': cls.course.id,
                'batch_id': hc_batch.id,
                'admission_date': date(2026, 5, 7),
                'partner_id': cls.partner.id,
                'state': 'done',
            })
            cls.hc_gradebook = cls.env['app.gradebook.student'].create({
                'partner_id': cls.partner.id,
                'course_id': cls.course.id,
                'batch_id': hc_batch.id,
                'admission_id': hc_admission.id,
            })
            faculty = cls.env['op.faculty'].create({
                'name': 'API Faculty',
                'first_name': 'API',
                'last_name': 'Faculty',
                'birth_date': date(1980, 1, 1),
                'gender': 'male',
            })
            cls.hc_session = cls.env['op.session'].create({
                'name': 'API HC Session',
                'course_id': cls.course.id,
                'batch_id': hc_batch.id,
                'subject_id': cls.subject.id,
                'start_datetime': fields.Datetime.now(),
                'end_datetime': fields.Datetime.now(),
                'faculty_id': faculty.id,
            })

    def setUp(self):
        super().setUp()
        if not getattr(self, '_certs_available', False):
            self.skipTest('Gradebook certificates are not installed.')

    def _payload(self, **overrides):
        data = {
            'gradebook_student_id': self.gradebook.id,
            'document_type': 'gradebook_partial',
            'certificate_type': 'digital',
            'signer': 'dpto_academico',
        }
        data.update(overrides)
        return data

    def _patch_pdf(self):
        return patch.object(
            type(self.env['irg.certificate.request']),
            '_convert_to_pdf',
            return_value=PDF_BYTES,
        )

    def _patch_diploma_pdf(self):
        return patch.object(
            type(self.env['irg.certificate.request']),
            '_generate_diploma_pdf_content',
            return_value=PDF_BYTES,
        )

    def _patch_attendance_pdf(self):
        Request = type(self.env['irg.certificate.request'])
        stack = ExitStack()
        stack.enter_context(patch.object(
            Request, '_fill_template', return_value='/tmp/irg-api-cert-stub.docx',
        ))
        stack.enter_context(patch.object(
            Request, '_convert_to_pdf', return_value=PDF_BYTES,
        ))
        return stack

    def _assert_verified_private_pdf(self, op, document_type):
        op.invalidate_recordset()
        data = self.result_json(op)
        self.assertEqual(op.state, 'verified')
        self.assertEqual(data['checksum'], PDF_CHECKSUM)
        raw = base64.b64decode(data['file_b64'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), data['checksum'])
        self.assertFalse(data['public'])
        cert = self.env['irg.certificate.request'].browse(data['certificate_request_id'])
        self.assertEqual(cert.document_type, document_type)
        self.assertEqual(cert.origin, 'backend')
        self.assertFalse(cert.invoice_id)
        attachment = self.env['ir.attachment'].browse(data['attachment_id'])
        self.assertFalse(attachment.public)
        return cert, data

    def test_unknown_payload_key_rejected(self):
        with self.assertRaises(UserError):
            self.run_op('irg_generate_gradebook_certificate', self._payload(sudo=True))

    def test_missing_signer_rejected(self):
        payload = self._payload()
        payload.pop('signer')
        with self.assertRaises(UserError):
            self.run_op('irg_generate_gradebook_certificate', payload, key='cert-no-signer')

    def test_invalid_signer_rejected(self):
        with self.assertRaises(UserError):
            self.run_op(
                'irg_generate_gradebook_certificate',
                self._payload(signer='someone_else'),
                key='cert-bad-signer',
            )

    def test_final_certificate_requires_done_gradebook(self):
        if self.gradebook.state == 'done':
            self.skipTest('Gradebook fixture already done.')
        with self.assertRaises(UserError):
            self.run_op(
                'irg_generate_gradebook_certificate',
                self._payload(document_type='gradebook'),
                key='cert-final-open',
            )

    def test_partial_allows_open_gradebook(self):
        op = self.run_op(
            'irg_generate_gradebook_certificate',
            self._payload(),
            key='cert-partial-open',
        )
        self.assertEqual(op.state, 'preview')
        proposed = self.proposed_json(op)
        self.assertEqual(proposed['document_type'], 'gradebook_partial')
        self.assertEqual(proposed['signer'], 'dpto_academico')
        self.assertNotIn('file_b64', proposed)

    def test_physical_requires_shipping(self):
        with self.assertRaises(UserError):
            self.run_op(
                'irg_generate_gradebook_certificate',
                self._payload(certificate_type='physical'),
                key='cert-phys-no-ship',
            )

    def test_approve_returns_private_pdf_and_checksum(self):
        op = self.run_op(
            'irg_generate_gradebook_certificate',
            self._payload(),
            key='cert-ok-1',
        )
        with self._patch_pdf():
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='cert-ok-1-ok')
        op.invalidate_recordset()
        data = self.result_json(op)
        self.assertEqual(op.state, 'verified')
        self.assertTrue(data['certificate_request_id'])
        self.assertTrue(data['attachment_id'])
        self.assertEqual(data['state'], 'done')
        self.assertTrue(data['name'])
        self.assertEqual(data['checksum'], PDF_CHECKSUM)
        raw = base64.b64decode(data['file_b64'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), data['checksum'])
        self.assertFalse(data['public'])
        attachment = self.env['ir.attachment'].browse(data['attachment_id'])
        self.assertFalse(attachment.public)
        cert = self.env['irg.certificate.request'].browse(data['certificate_request_id'])
        self.assertEqual(cert.origin, 'backend')
        self.assertFalse(cert.invoice_id)

    def test_same_idempotency_key_does_not_duplicate(self):
        payload = self._payload()
        first = self.run_op('irg_generate_gradebook_certificate', payload, key='cert-idem')
        with self._patch_pdf():
            self.run_op('irg_approve_operation', {'operation_id': first.id}, key='cert-idem-ok')
        first.invalidate_recordset()
        cert_id = self.result_json(first)['certificate_request_id']
        second = self.run_op('irg_generate_gradebook_certificate', payload, key='cert-idem')
        self.assertEqual(second.id, first.id)
        copies = self.env['irg.certificate.request'].search([
            ('gradebook_student_id', '=', self.gradebook.id),
            ('origin', '=', 'backend'),
        ])
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies.id, cert_id)

    def test_approve_does_not_queue_certificate_mail(self):
        Mail = self.env['mail.mail']
        before = Mail.search_count([])
        op = self.run_op(
            'irg_generate_gradebook_certificate',
            self._payload(),
            key='cert-no-mail',
        )
        with self._patch_pdf():
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='cert-no-mail-ok')
        self.assertEqual(Mail.search_count([]), before)

    def test_enrollment_allows_open_gradebook(self):
        op = self.run_op(
            'irg_generate_gradebook_certificate',
            self._payload(document_type='enrollment'),
            key='cert-enroll-open',
        )
        self.assertEqual(op.state, 'preview')
        proposed = self.proposed_json(op)
        self.assertEqual(proposed['document_type'], 'enrollment')
        self.assertEqual(
            proposed['will_call'],
            'irg.certificate.request._generate_and_attach_pdf',
        )
        self.assertNotIn('file_b64', proposed)

    def test_enrollment_approve_returns_private_pdf(self):
        op = self.run_op(
            'irg_generate_gradebook_certificate',
            self._payload(document_type='enrollment'),
            key='cert-enroll-ok',
        )
        with self._patch_pdf():
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='cert-enroll-ok-ok')
        self._assert_verified_private_pdf(op, 'enrollment')

    def test_diploma_requires_done_gradebook(self):
        if self.gradebook.state == 'done':
            self.skipTest('Gradebook fixture already done.')
        with self.assertRaises(UserError) as ctx:
            self.run_op(
                'irg_generate_gradebook_certificate',
                self._payload(document_type='diploma'),
                key='cert-diploma-open',
            )
        self.assertIn('finalizada', str(ctx.exception).lower())

    def test_diploma_approve_on_done_gradebook(self):
        self.gradebook.write({'state': 'done'})
        op = self.run_op(
            'irg_generate_gradebook_certificate',
            self._payload(document_type='diploma'),
            key='cert-diploma-ok',
        )
        with self._patch_diploma_pdf():
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='cert-diploma-ok-ok')
        self._assert_verified_private_pdf(op, 'diploma')

    def test_session_id_rejected_unless_attendance(self):
        with self.assertRaises(UserError) as ctx:
            self.run_op(
                'irg_generate_gradebook_certificate',
                self._payload(document_type='enrollment', session_id=1),
                key='cert-session-enroll',
            )
        self.assertIn('attendance', str(ctx.exception).lower())

    def test_attendance_requires_session_id(self):
        if not self._attendance_available:
            self.skipTest('Attendance certificates are not installed.')
        with self.assertRaises(UserError) as ctx:
            self.run_op(
                'irg_generate_gradebook_certificate',
                self._payload(
                    document_type='attendance',
                    gradebook_student_id=self.hc_gradebook.id,
                ),
                key='cert-att-no-session',
            )
        self.assertIn('session', str(ctx.exception).lower())

    def test_attendance_without_module_is_rejected(self):
        if self._attendance_available:
            self.skipTest('Attendance module is installed.')
        with self.assertRaises(UserError) as ctx:
            self.run_op(
                'irg_generate_gradebook_certificate',
                self._payload(document_type='attendance'),
                key='cert-att-missing-mod',
            )
        self.assertIn('attendance', str(ctx.exception).lower())

    def test_attendance_approve_on_hc_batch(self):
        if not self._attendance_available:
            self.skipTest('Attendance certificates are not installed.')
        op = self.run_op(
            'irg_generate_gradebook_certificate',
            self._payload(
                document_type='attendance',
                gradebook_student_id=self.hc_gradebook.id,
                session_id=self.hc_session.id,
            ),
            key='cert-att-ok',
        )
        with self._patch_attendance_pdf():
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='cert-att-ok-ok')
        cert, _data = self._assert_verified_private_pdf(op, 'attendance')
        self.assertEqual(cert.session_id.id, self.hc_session.id)
