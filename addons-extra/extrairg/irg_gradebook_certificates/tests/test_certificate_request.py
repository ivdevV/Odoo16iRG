# -*- coding: utf-8 -*-
from zipfile import ZipFile

from docx import Document as DocxDocument

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError, UserError


class TestIrgCertificateRequest(TransactionCase):
    """Basic integration tests for irg.certificate.request."""

    def _assert_bottom_right_arcs_are_visible_in_xml(self, res_file):
        with ZipFile(res_file) as docx_zip:
            document_xml = docx_zip.read('word/document.xml').decode(
                'utf-8', errors='ignore'
            )
            rels_xml = docx_zip.read('word/_rels/document.xml.rels').decode(
                'utf-8', errors='ignore'
            )
            package_names = set(docx_zip.namelist())

        self.assertIn('name="Bottom Right Arcs"', document_xml)
        self.assertIn('behindDoc="1"', document_xml)
        self.assertIn('relativeFrom="page"><wp:align>right</wp:align>', document_xml)
        self.assertIn('relativeFrom="page"><wp:align>bottom</wp:align>', document_xml)
        self.assertIn('Target="media/bottom_right_arcs.png"', rels_xml)
        self.assertIn('word/media/bottom_right_arcs.png', package_names)

    def _assert_vertical_legal_text_is_visible_in_xml(self, res_file):
        with ZipFile(res_file) as docx_zip:
            document_xml = ''.join(
                docx_zip.read(name).decode('utf-8', errors='ignore')
                for name in docx_zip.namelist()
                if name.endswith('.xml')
            )

        self.assertIn('B56488687', document_xml)
        self.assertIn('B-603323', document_xml)
        self.assertIn('w:val="10"', document_xml)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create minimal linked records
        cls.partner = cls.env['res.partner'].create({'name': 'Test Student Portal'})
        cls.course = cls.env['op.course'].create({'name': 'Test Course', 'code': 'TC01'})
        cls.batch = cls.env['op.batch'].create({
            'name': 'Batch A',
            'code': 'BA',
            'course_id': cls.course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Test Course Product',
            'type': 'service',
        })
        cls.register = cls.env['op.admission.register'].create({
            'name': 'Test Register',
            'course_id': cls.course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.admission = cls.env['op.admission'].create({
            'name': 'ADM-TEST',
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'register_id': cls.register.id,
            'gender': 'm',
            'first_name': 'Test',
            'last_name': 'Student',
            'email': 'test.certificate@example.com',
            'birth_date': '1990-01-01',
        })
        cls.gradebook = cls.env['app.gradebook.student'].create({
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'admission_id': cls.admission.id,
        })

    # ------------------------------------------------------------------
    # Sequence
    # ------------------------------------------------------------------

    def test_01_sequence_assigned_on_create(self):
        """name should be populated from ir.sequence, not stay 'New'."""
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'digital',
            'state': 'draft',
        })
        self.assertNotEqual(cert.name, 'New', 'Sequence was not assigned on create.')
        self.assertTrue(cert.name.startswith('CERT/'), 'Sequence prefix mismatch.')

    # ------------------------------------------------------------------
    # Price computation
    # ------------------------------------------------------------------

    def test_02_digital_price_no_shipping(self):
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'digital',
            'state': 'draft',
        })
        self.assertAlmostEqual(cert.price_base, 30.0)
        self.assertAlmostEqual(cert.price_shipping, 0.0)
        self.assertAlmostEqual(cert.price_total, 30.0)

    def test_03_physical_national_price(self):
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'physical',
            'shipping_type': 'national',
            'state': 'draft',
        })
        self.assertAlmostEqual(cert.price_base, 40.0)
        self.assertAlmostEqual(cert.price_shipping, 20.0)
        self.assertAlmostEqual(cert.price_total, 60.0)

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------

    def test_04_physical_without_shipping_raises(self):
        with self.assertRaises(ValidationError):
            self.env['irg.certificate.request'].create({
                'gradebook_student_id': self.gradebook.id,
                'certificate_type': 'physical',
                # shipping_type intentionally omitted
                'state': 'draft',
            })

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def test_05_cancel_draft(self):
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'digital',
            'state': 'draft',
        })
        cert.action_cancel()
        self.assertEqual(cert.state, 'cancelled')

    def test_06_cannot_cancel_done(self):
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'digital',
            'state': 'done',
        })
        with self.assertRaises(UserError):
            cert.action_cancel()

    def test_07_process_payment_physical(self):
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'physical',
            'shipping_type': 'national',
            'state': 'pending_payment',
        })
        cert._process_payment()
        self.assertEqual(cert.state, 'paid', 'Physical cert should be in "paid" after payment.')

    # ------------------------------------------------------------------
    # app.gradebook.student inherit
    # ------------------------------------------------------------------

    def test_08_certificate_count(self):
        initial_count = self.gradebook.certificate_count
        self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'digital',
            'state': 'done',
        })
        self.gradebook.invalidate_recordset(['certificate_count'])
        self.assertEqual(self.gradebook.certificate_count, initial_count + 1)

    def test_09_bottom_right_arcs_are_added_to_base_word_certificates(self):
        for document_type in ('gradebook', 'attendance', 'enrollment'):
            cert = self.env['irg.certificate.request'].create({
                'gradebook_student_id': self.gradebook.id,
                'certificate_type': 'digital',
                'document_type': document_type,
                'state': 'draft',
            })
            res_file = cert._fill_template()
            self._assert_bottom_right_arcs_are_visible_in_xml(res_file)

    def test_10_final_gradebook_layout_matches_partial_structure(self):
        for signer, signature_lines in (
            ('raimon', ['Raimon Gaja Jaumeandreu', 'Instituto Raimon Gaja']),
            ('dpto_academico', ['Departamento Académico', 'Instituto Raimon Gaja']),
        ):
            cert = self.env['irg.certificate.request'].create({
                'gradebook_student_id': self.gradebook.id,
                'certificate_type': 'digital',
                'document_type': 'gradebook',
                'signer': signer,
                'state': 'draft',
            })

            res_file = cert._fill_template()
            self._assert_vertical_legal_text_is_visible_in_xml(res_file)
            document = DocxDocument(res_file)

            certifica = next(
                (para for para in document.paragraphs if para.text.strip() == 'CERTIFICA:'),
                None,
            )
            closing = next(
                (
                    para for para in document.paragraphs
                    if 'Para que así conste' in para.text
                ),
                None,
            )
            signature_paragraph = next(
                (
                    para for para in document.paragraphs
                    if para.text.splitlines() == signature_lines
                ),
                None,
            )
            first_body = next(
                (
                    para for para in document.paragraphs
                    if para.text.startswith('Que Test Student Portal con')
                ),
                None,
            )
            second_body = next(
                (
                    para for para in document.paragraphs
                    if para.text.startswith('Que, el Máster consta de')
                ),
                None,
            )
            third_body = next(
                (
                    para for para in document.paragraphs
                    if para.text == 'Las calificaciones obtenidas son:'
                ),
                None,
            )

            self.assertIsNotNone(certifica)
            self.assertEqual(certifica.alignment, 0)
            self.assertEqual(certifica.paragraph_format.left_indent.twips, -172)
            self.assertEqual(certifica.paragraph_format.right_indent.twips, -783)
            self.assertIsNotNone(first_body)
            self.assertIn(' consta matriculado/a en el ', first_body.text)
            self.assertIn('durante el período académico', first_body.text)
            self.assertNotIn('ha obtenido las calificaciones siguientes', first_body.text)
            self.assertEqual(first_body.alignment, 3)
            self.assertEqual(first_body.paragraph_format.left_indent.twips, -172)
            self.assertEqual(first_body.paragraph_format.right_indent.twips, -783)
            bold_runs = [run.text for run in first_body.runs if run.bold]
            self.assertIn('Test Student Portal', bold_runs)
            self.assertIn('Test Course', bold_runs)
            self.assertIsNotNone(second_body)
            self.assertIn(
                '60 ECTS, equivalentes a 1500 horas de estudio',
                second_body.text,
            )
            self.assertEqual(second_body.alignment, 3)
            self.assertEqual(second_body.paragraph_format.left_indent.twips, -172)
            self.assertEqual(second_body.paragraph_format.right_indent.twips, -783)
            self.assertIsNotNone(third_body)
            self.assertEqual(third_body.alignment, 3)
            self.assertEqual(third_body.paragraph_format.left_indent.twips, -172)
            self.assertEqual(third_body.paragraph_format.right_indent.twips, -783)
            self.assertIsNotNone(closing)
            self.assertEqual(closing.alignment, 3)
            self.assertEqual(closing.paragraph_format.left_indent.twips, -172)
            self.assertEqual(closing.paragraph_format.right_indent.twips, -783)
            self.assertIsNotNone(signature_paragraph)
            self.assertEqual(signature_paragraph.text.splitlines(), signature_lines)
            self.assertEqual(signature_paragraph.alignment, 0)
            self.assertEqual(signature_paragraph.paragraph_format.left_indent.twips, -172)
            self.assertEqual(signature_paragraph.paragraph_format.right_indent.twips, -783)
