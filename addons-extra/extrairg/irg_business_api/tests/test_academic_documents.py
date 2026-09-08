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
class TestAcademicDocumentOperations(IrgBusinessApiCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._diploma_available = 'irg.diploma.wizard' in cls.env
        cls._certs_available = (
            'app.gradebook.student' in cls.env and 'irg.certificate.request' in cls.env
        )
        cls.student = False
        cls.student_course = False
        cls.gradebook = False
        if 'op.student' in cls.env:
            cls.student = cls.env['op.student'].create({
                'first_name': 'API',
                'last_name': 'Diploma',
                'gender': 'o',
                'birth_date': date(1990, 1, 1),
                'partner_id': cls.partner.id,
            })
            course_vals = {
                'student_id': cls.student.id,
                'course_id': cls.course.id,
                'batch_id': cls.batch.id,
            }
            if 'state' in cls.env['op.student.course']._fields:
                course_vals['state'] = 'finished'
            cls.student_course = cls.env['op.student.course'].create(course_vals)
        if cls._certs_available:
            tmpl_vals = {'name': 'API Doc Template'}
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
        cls._attendance_available = (
            cls._certs_available
            and 'session_id' in cls.env['irg.certificate.request']._fields
            and 'op.session' in cls.env
            and 'op.faculty' in cls.env
        )
        cls.hc_admission = False
        cls.hc_session = False
        if cls._attendance_available:
            hc_batch = cls.env['op.batch'].create({
                'name': 'API Batch HC',
                'code': 'APIHC%s' % cls.batch.code[-4:],
                'course_id': cls.course.id,
                'start_date': date(2026, 1, 1),
                'end_date': date(2026, 12, 31),
            })
            cls.hc_admission = cls.env['op.admission'].create({
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
            cls.env['app.gradebook.student'].create({
                'partner_id': cls.partner.id,
                'course_id': cls.course.id,
                'batch_id': hc_batch.id,
                'admission_id': cls.hc_admission.id,
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

    def _assert_private_pdf(self, op):
        op.invalidate_recordset()
        data = self.result_json(op)
        self.assertEqual(op.state, 'verified')
        self.assertEqual(data['checksum'], PDF_CHECKSUM)
        raw = base64.b64decode(data['file_b64'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), data['checksum'])
        self.assertFalse(data['public'])
        attachment = self.env['ir.attachment'].browse(data['attachment_id'])
        self.assertFalse(attachment.public)
        return data

    def test_diploma_unknown_payload_key_rejected(self):
        if not self._diploma_available or not self.student_course:
            self.skipTest('Diploma wizard is not installed.')
        with self.assertRaises(UserError):
            self.run_op(
                'irg_generate_diploma',
                {
                    'student_id': self.student.id,
                    'student_course_id': self.student_course.id,
                    'diploma_type': 'digital',
                    'sudo': True,
                },
                key='dip-bad-key',
            )

    def test_diploma_preview_has_no_gradebook_and_no_pdf(self):
        if not self._diploma_available or not self.student_course:
            self.skipTest('Diploma wizard is not installed.')
        op = self.run_op(
            'irg_generate_diploma',
            {
                'student_id': self.student.id,
                'student_course_id': self.student_course.id,
                'diploma_type': 'digital',
            },
            key='dip-preview',
        )
        self.assertEqual(op.state, 'preview')
        proposed = self.proposed_json(op)
        self.assertEqual(proposed['student_id'], self.student.id)
        self.assertEqual(proposed['student_course_id'], self.student_course.id)
        self.assertNotIn('gradebook_student_id', proposed)
        self.assertNotIn('file_b64', proposed)
        self.assertEqual(proposed['course_state'], 'finished')
        self.assertEqual(proposed['will_call'], 'irg.diploma.wizard.action_print_diploma')
        self.assertEqual(proposed['will_create'], 'irg.diploma.registry')

    def test_diploma_rejects_running_course(self):
        if not self._diploma_available or not self.student_course:
            self.skipTest('Diploma wizard is not installed.')
        if 'state' not in self.student_course._fields:
            self.skipTest('op.student.course has no state.')
        self.student_course.write({'state': 'running'})
        try:
            with self.assertRaises(UserError) as ctx:
                self.run_op(
                    'irg_generate_diploma',
                    {
                        'student_id': self.student.id,
                        'student_course_id': self.student_course.id,
                        'diploma_type': 'digital',
                    },
                    key='dip-running',
                )
            self.assertIn('finished', str(ctx.exception).lower())
        finally:
            self.student_course.write({'state': 'finished'})

    def test_diploma_approve_returns_private_pdf(self):
        if not self._diploma_available or not self.student_course:
            self.skipTest('Diploma wizard is not installed.')
        op = self.run_op(
            'irg_generate_diploma',
            {
                'student_id': self.student.id,
                'student_course_id': self.student_course.id,
                'diploma_type': 'digital',
            },
            key='dip-ok',
        )
        Report = type(self.env['report.irg_generacion_diplomas.diploma_pdf'])
        with patch.object(Report, 'generate_diploma_pdf', return_value=PDF_BYTES):
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='dip-ok-ok')
        data = self._assert_private_pdf(op)
        self.assertTrue(data.get('diploma_registry_id'))
        self.assertNotIn('gradebook_student_id', data)

    def test_enrollment_uses_admission_not_gradebook_payload(self):
        if not self._certs_available:
            self.skipTest('Gradebook certificates are not installed.')
        op = self.run_op(
            'irg_generate_enrollment_certificate',
            {
                'admission_id': self.admission.id,
                'certificate_type': 'digital',
                'signer': 'dpto_academico',
            },
            key='enroll-preview',
        )
        self.assertEqual(op.state, 'preview')
        proposed = self.proposed_json(op)
        self.assertEqual(proposed['admission_id'], self.admission.id)
        self.assertNotIn('gradebook_student_id', proposed)
        self.assertNotIn('file_b64', proposed)

    def test_enrollment_approve_returns_private_pdf(self):
        if not self._certs_available:
            self.skipTest('Gradebook certificates are not installed.')
        op = self.run_op(
            'irg_generate_enrollment_certificate',
            {
                'admission_id': self.admission.id,
                'certificate_type': 'digital',
                'signer': 'dpto_academico',
            },
            key='enroll-ok',
        )
        with patch.object(
            type(self.env['irg.certificate.request']),
            '_convert_to_pdf',
            return_value=PDF_BYTES,
        ):
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='enroll-ok-ok')
        data = self._assert_private_pdf(op)
        cert = self.env['irg.certificate.request'].browse(data['certificate_request_id'])
        self.assertEqual(cert.document_type, 'enrollment')
        self.assertEqual(cert.origin, 'backend')
        self.assertNotIn('gradebook_student_id', data)

    def test_attendance_requires_session_id(self):
        if not self._attendance_available:
            self.skipTest('Attendance certificates are not installed.')
        with self.assertRaises(UserError) as ctx:
            self.run_op(
                'irg_generate_attendance_certificate',
                {
                    'admission_id': self.hc_admission.id,
                    'certificate_type': 'digital',
                    'signer': 'dpto_academico',
                },
                key='att-no-session',
            )
        self.assertIn('session', str(ctx.exception).lower())

    def test_attendance_approve_on_hc_admission(self):
        if not self._attendance_available:
            self.skipTest('Attendance certificates are not installed.')
        op = self.run_op(
            'irg_generate_attendance_certificate',
            {
                'admission_id': self.hc_admission.id,
                'session_id': self.hc_session.id,
                'certificate_type': 'digital',
                'signer': 'dpto_academico',
            },
            key='att-ok',
        )
        Request = type(self.env['irg.certificate.request'])
        with ExitStack() as stack:
            stack.enter_context(patch.object(
                Request, '_fill_template', return_value='/tmp/irg-api-cert-stub.docx',
            ))
            stack.enter_context(patch.object(
                Request, '_convert_to_pdf', return_value=PDF_BYTES,
            ))
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='att-ok-ok')
        data = self._assert_private_pdf(op)
        cert = self.env['irg.certificate.request'].browse(data['certificate_request_id'])
        self.assertEqual(cert.document_type, 'attendance')
        self.assertEqual(cert.session_id.id, self.hc_session.id)
        self.assertNotIn('gradebook_student_id', data)
