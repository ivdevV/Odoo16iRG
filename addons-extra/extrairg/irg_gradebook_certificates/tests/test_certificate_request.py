# -*- coding: utf-8 -*-
import os
import hashlib
from zipfile import ZipFile
from lxml import etree

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
                    if [line.strip() for line in para.text.splitlines()] == signature_lines
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
            self.assertEqual([line.strip() for line in signature_paragraph.text.splitlines()], signature_lines)
            self.assertEqual(signature_paragraph.alignment, 0)
            self.assertEqual(signature_paragraph.paragraph_format.left_indent.twips, -172)
            self.assertEqual(signature_paragraph.paragraph_format.right_indent.twips, -783)

    def _assert_bottom_right_arcs_are_absent_in_xml(self, res_file):
        with ZipFile(res_file) as docx_zip:
            document_xml = docx_zip.read('word/document.xml').decode(
                'utf-8', errors='ignore'
            )
            rels_xml = docx_zip.read('word/_rels/document.xml.rels').decode(
                'utf-8', errors='ignore'
            )
            package_names = set(docx_zip.namelist())

        self.assertNotIn('name="Bottom Right Arcs"', document_xml)
        self.assertNotIn('Target="media/bottom_right_arcs.png"', rels_xml)
        self.assertNotIn('word/media/bottom_right_arcs.png', package_names)

    def _assert_header_logo_is_removed_in_xml(self, res_file):
        header_name = 'word/header1.xml'
        with ZipFile(res_file) as docx_zip:
            if header_name not in docx_zip.namelist():
                return
            header_xml = etree.fromstring(docx_zip.read(header_name))
        
        runs_with_drawings = []
        for r in header_xml.xpath('.//*[local-name()="r"]'):
            if r.xpath('.//*[local-name()="drawing" or local-name()="AlternateContent" or local-name()="pict"]'):
                runs_with_drawings.append(r)
        self.assertEqual(len(runs_with_drawings), 0, "Header logo drawings were not removed.")

    def _assert_header_logo_is_present_in_xml(self, res_file):
        header_name = 'word/header1.xml'
        with ZipFile(res_file) as docx_zip:
            if header_name not in docx_zip.namelist():
                self.fail("Header XML not found in document.")
            header_xml = etree.fromstring(docx_zip.read(header_name))
        
        runs_with_drawings = []
        for r in header_xml.xpath('.//*[local-name()="r"]'):
            if r.xpath('.//*[local-name()="drawing" or local-name()="AlternateContent" or local-name()="pict"]'):
                runs_with_drawings.append(r)
        self.assertTrue(len(runs_with_drawings) > 0, "Header logo drawings were removed but should be present.")

    def test_11_physical_gradebook_omits_logo_and_arcs(self):
        """Physical/apostilled gradebook certificates must omit the header logo and decorative arcs."""
        for cert_type in ('physical', 'physical_apostilled'):
            cert = self.env['irg.certificate.request'].create({
                'gradebook_student_id': self.gradebook.id,
                'document_type': 'gradebook',
                'certificate_type': cert_type,
                'shipping_type': 'national',
                'state': 'draft',
            })
            res_file = cert._fill_template()
            self._assert_bottom_right_arcs_are_absent_in_xml(res_file)
            self._assert_header_logo_is_removed_in_xml(res_file)

    def test_12_non_physical_gradebook_retains_logo_and_arcs(self):
        """Digital/custom gradebook certificates must retain the header logo and decorative arcs."""
        for cert_type in ('digital', 'custom'):
            cert = self.env['irg.certificate.request'].create({
                'gradebook_student_id': self.gradebook.id,
                'document_type': 'gradebook',
                'certificate_type': cert_type,
                'state': 'draft',
            })
            res_file = cert._fill_template()
            self._assert_bottom_right_arcs_are_visible_in_xml(res_file)
            self._assert_header_logo_is_present_in_xml(res_file)

    def _assert_table_font_sizes_match_top_font_size(self, res_file):
        doc = DocxDocument(res_file)
        top_font_size = None
        for para in doc.paragraphs:
            if para.text.strip():
                for r in para.runs:
                    if r.font and r.font.size:
                        top_font_size = r.font.size
                        break
            if top_font_size:
                break
        self.assertIsNotNone(top_font_size, "Could not find top font size in document.")
        for tbl in doc.tables:
            for row in tbl.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        for run in para.runs:
                            self.assertEqual(
                                run.font.size,
                                top_font_size,
                                "Table run font size does not match calculated top font size."
                            )

    def _assert_signature_logo_is_present_and_referenced(self, res_file):
        module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(module_path, 'static', 'src', 'img', 'logodesgastado.png')
        self.assertTrue(os.path.isfile(logo_path), "Expected signature logo does not exist in module path.")
        with open(logo_path, 'rb') as f:
            expected_md5 = hashlib.md5(f.read()).hexdigest()

        with ZipFile(res_file) as z:
            matching_media_file = None
            for name in z.namelist():
                if name.startswith('word/media/'):
                    data = z.read(name)
                    if hashlib.md5(data).hexdigest() == expected_md5:
                        matching_media_file = name
                        break
            self.assertIsNotNone(matching_media_file, "logodesgastado.png not found by MD5 hash inside ZIP media.")
            
            doc_xml = z.read('word/document.xml').decode('utf-8', errors='ignore')
            rels_xml = z.read('word/_rels/document.xml.rels').decode('utf-8', errors='ignore')
            
        relative_target = matching_media_file.replace('word/', '')
        import re
        r_ids = re.findall(rf'Id="([^"]+)"[^>]+Target="{re.escape(relative_target)}"', rels_xml)
        self.assertTrue(len(r_ids) > 0, f"Relationship for {relative_target} not found in document.xml.rels")
        
        referenced = any(r_id in doc_xml for r_id in r_ids)
        self.assertTrue(referenced, f"Relationship ID(s) {r_ids} for signature logo not referenced in document.xml")

    def test_13_table_font_sizes_match_top_font_size(self):
        """Verify that table cell font size matches the top font size for all document formats."""
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'digital',
            'document_type': 'gradebook',
            'state': 'draft',
        })
        res_file = cert._fill_template()
        self._assert_table_font_sizes_match_top_font_size(res_file)

        cert_phys = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'physical',
            'shipping_type': 'national',
            'document_type': 'gradebook',
            'state': 'draft',
        })
        res_file_phys = cert_phys._fill_template()
        self._assert_table_font_sizes_match_top_font_size(res_file_phys)

    def test_14_signature_logo_present_for_raimon_signer(self):
        """Verify that Raimon Gaja's signature logo is present in the ZIP and referenced in document.xml."""
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'certificate_type': 'digital',
            'document_type': 'gradebook',
            'signer': 'raimon',
            'state': 'draft',
        })
        res_file = cert._fill_template()
        self._assert_signature_logo_is_present_and_referenced(res_file)


