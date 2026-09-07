# -*- coding: utf-8 -*-
import base64
import hashlib
from unittest.mock import patch

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
