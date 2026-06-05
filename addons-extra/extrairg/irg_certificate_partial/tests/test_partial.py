# -*- coding: utf-8 -*-
from zipfile import ZipFile

from docx import Document as DocxDocument
from lxml import etree

from odoo import fields
from odoo.tests.common import TransactionCase


class TestIrgCertificatePartial(TransactionCase):

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

    def _assert_corner_decoration_is_visible_in_xml(self, res_file):
        with ZipFile(res_file) as docx_zip:
            document_xml = etree.fromstring(docx_zip.read('word/document.xml'))
            rels_xml = etree.fromstring(docx_zip.read('word/_rels/document.xml.rels'))
            package_names = set(docx_zip.namelist())

        closing_paragraphs = document_xml.xpath(
            './/*[local-name()="body"]/*[local-name()="p" and '
            './/*[local-name()="t" and contains(text(), "Para que así conste")]]'
        )
        self.assertTrue(closing_paragraphs)
        paragraphs = document_xml.xpath('.//*[local-name()="body"]/*[local-name()="p"]')
        closing_index = paragraphs.index(closing_paragraphs[0])
        image_rel_ids = []
        for paragraph in paragraphs[closing_index:closing_index + 3]:
            image_rel_ids.extend(
                paragraph.xpath('.//*[local-name()="blip"]/@*[local-name()="embed"]')
            )
        self.assertTrue(image_rel_ids)

        targets_by_rel_id = {rel.get('Id'): rel.get('Target') for rel in rels_xml}
        for rel_id in image_rel_ids:
            target = targets_by_rel_id.get(rel_id)
            self.assertTrue(target)
            self.assertIn('word/%s' % target, package_names)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create student and course
        cls.partner = cls.env['res.partner'].create({'name': 'Test Student Partial'})
        cls.course = cls.env['op.course'].create({'name': 'Test Course Partial', 'code': 'TCPART01'})
        cls.batch = cls.env['op.batch'].create({
            'name': 'Batch Partial',
            'code': 'BPPART',
            'course_id': cls.course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
        })

        # Admissions
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product Partial',
            'type': 'service',
        })
        cls.register = cls.env['op.admission.register'].create({
            'name': 'Test Register Partial',
            'course_id': cls.course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
            'product_id': cls.product.id,
        })
        cls.admission = cls.env['op.admission'].create({
            'name': 'ADM-TEST-PARTIAL',
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'register_id': cls.register.id,
            'gender': 'm',
            'first_name': 'Test',
            'last_name': 'Student',
            'email': 'test.partial@example.com',
            'birth_date': '1990-01-01',
        })

        # Gradebook template config
        cls.gradebook_tmpl = cls.env['app.gradebook'].create({
            'name': 'Gradebook Template Test',
            'gradebook_template_ids': [(0, 0, {
                'type': 'exam',
                'qty': 2,
                'weight': 100,
            })]
        })
        # Link template to course
        cls.course.write({'gradebook_id': cls.gradebook_tmpl.id})
        cls.tmpl_line = cls.gradebook_tmpl.gradebook_template_ids[0]

        # Gradebooks
        cls.gradebook = cls.env['app.gradebook.student'].create({
            'partner_id': cls.partner.id,
            'course_id': cls.course.id,
            'batch_id': cls.batch.id,
            'admission_id': cls.admission.id,
        })

        # Subjects
        cls.subject_normal = cls.env['op.subject'].create({
            'name': 'Subject Compulsory A',
            'code': 'SCA',
            'course_id': cls.course.id,
            'subject_type': 'compulsory',
        })
        cls.subject_pending = cls.env['op.subject'].create({
            'name': 'Subject Compulsory B',
            'code': 'SCB',
            'course_id': cls.course.id,
            'subject_type': 'compulsory',
        })

        # Link subjects to student gradebook
        cls.gb_subj_a = cls.env['app.gradebook.subject'].create({
            'gradebook_student_id': cls.gradebook.id,
            'op_subject_id': cls.subject_normal.id,
        })
        cls.gb_subj_b = cls.env['app.gradebook.subject'].create({
            'gradebook_student_id': cls.gradebook.id,
            'op_subject_id': cls.subject_pending.id,
        })

        # Create results for Subject A (2 exams, so it's complete)
        cls.env['app.gradebook.result'].create({
            'gradebook_subject_id': cls.gb_subj_a.id,
            'survey_type': 'exam',
            'scoring_total': 8.5,
        })
        cls.env['app.gradebook.result'].create({
            'gradebook_subject_id': cls.gb_subj_a.id,
            'survey_type': 'exam',
            'scoring_total': 9.5,
        })
        # Force computation
        cls.gb_subj_a.compute_final_subject_note()
        cls.gb_subj_a.compute_point_average()

        # Create only 1 result for Subject B (2 exams required, so it's incomplete / pending)
        cls.env['app.gradebook.result'].create({
            'gradebook_subject_id': cls.gb_subj_b.id,
            'survey_type': 'exam',
            'scoring_total': 7.0,
        })
        # Force computation
        cls.gb_subj_b.compute_final_subject_note()
        cls.gb_subj_b.compute_point_average()

    def test_01_partial_gradebook_fill_template(self):
        """Check template filling logic for partial gradebooks."""
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'document_type': 'gradebook_partial',
            'certificate_type': 'digital',
            'state': 'draft',
        })
        # Run template filling logic
        res_file = cert._fill_template()
        self.assertTrue(res_file)

    def test_02_partial_gradebook_first_sentence_has_bold_student_and_course(self):
        """Student and course names are bold in the first descriptive line."""
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'document_type': 'gradebook_partial',
            'certificate_type': 'digital',
            'state': 'draft',
        })

        res_file = cert._fill_template()
        self._assert_vertical_legal_text_is_visible_in_xml(res_file)
        self._assert_corner_decoration_is_visible_in_xml(res_file)
        document = DocxDocument(res_file)
        paragraph = next(
            (
                para for para in document.paragraphs
                if 'Test Student Partial' in para.text
                and 'Test Course Partial' in para.text
            ),
            None,
        )

        self.assertIsNotNone(paragraph)
        self.assertIn(
            'Que Test Student Partial con DNI/Pasaporte  consta matriculado/a en '
            'el Test Course Partial durante el período académico',
            paragraph.text,
        )
        self.assertTrue(
            any(
                run.text == 'Test Student Partial' and run.bold is True
                for run in paragraph.runs
            )
        )
        self.assertTrue(
            any(
                run.text == 'Test Course Partial' and run.bold is True
                for run in paragraph.runs
            )
        )

    def test_03_partial_gradebook_dpto_intro_and_layout_are_adjusted(self):
        """Department signer uses requested issuer text and table-width layout."""
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'document_type': 'gradebook_partial',
            'certificate_type': 'digital',
            'signer': 'dpto_academico',
            'state': 'draft',
        })

        res_file = cert._fill_template()
        document = DocxDocument(res_file)

        intro = next(
            (
                para for para in document.paragraphs
                if 'El Instituto Raimon Gaja, con CIF B-56488687' in para.text
            ),
            None,
        )
        first_sentence = next(
            (
                para for para in document.paragraphs
                if 'Test Student Partial' in para.text
                and 'Test Course Partial' in para.text
            ),
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
                if 'Departamento Académico' in para.text
                and 'Instituto Raimon Gaja' in para.text
            ),
            None,
        )

        self.assertIsNotNone(intro)
        self.assertEqual(
            intro.text,
            'El Instituto Raimon Gaja, con CIF B-56488687 en calle '
            'Córcega 213, 1º 2ª, 08036 Barcelona.',
        )
        self.assertIsNotNone(intro)
        self.assertEqual(intro.alignment, 0)
        self.assertEqual(intro.paragraph_format.left_indent.twips, -172)
        self.assertEqual(intro.paragraph_format.right_indent.twips, -783)
        for paragraph in (first_sentence, closing):
            self.assertIsNotNone(paragraph)
            self.assertEqual(paragraph.alignment, 3)
            self.assertEqual(paragraph.paragraph_format.left_indent.twips, -172)
            self.assertEqual(paragraph.paragraph_format.right_indent.twips, -783)
        self.assertIsNotNone(signature_paragraph)
        self.assertEqual(
            signature_paragraph.text.splitlines(),
            ['Departamento Académico', 'Instituto Raimon Gaja'],
        )
        self.assertEqual(signature_paragraph.alignment, 0)
        self.assertEqual(signature_paragraph.paragraph_format.left_indent.twips, -172)
        self.assertEqual(signature_paragraph.paragraph_format.right_indent.twips, -783)

    def test_04_partial_gradebook_raimon_intro_certifica_and_signature_align_with_table(self):
        """Raimon signer header, CERTIFICA and signature use the same text grid."""
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'document_type': 'gradebook_partial',
            'certificate_type': 'digital',
            'signer': 'raimon',
            'state': 'draft',
        })

        res_file = cert._fill_template()
        document = DocxDocument(res_file)

        signer_intro = next(
            (
                para for para in document.paragraphs
                if 'Raimon Gaja Jaumeandreu' in para.text
                and 'Director General' in para.text
            ),
            None,
        )
        certifica = next(
            (para for para in document.paragraphs if para.text.strip() == 'CERTIFICA:'),
            None,
        )
        signature_name = next(
            (
                para for para in document.paragraphs
                if 'Raimon Gaja Jaumeandreu' in para.text
                and 'Instituto Raimon Gaja' in para.text
            ),
            None,
        )

        for paragraph in (signer_intro, certifica, signature_name):
            self.assertIsNotNone(paragraph)
            self.assertEqual(paragraph.paragraph_format.left_indent.twips, -172)
            self.assertEqual(paragraph.paragraph_format.right_indent.twips, -783)

    def test_05_partial_gradebook_all_pending_fill_template(self):
        """Check template filling logic when all compulsory subjects are pending."""
        # Unlink results for Subject A to make it pending too
        self.gb_subj_a.gradebook_result_ids.unlink()
        self.gb_subj_a.compute_final_subject_note()
        self.gb_subj_a.compute_point_average()

        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'document_type': 'gradebook_partial',
            'certificate_type': 'digital',
            'state': 'draft',
        })
        res_file = cert._fill_template()
        self.assertTrue(res_file)
