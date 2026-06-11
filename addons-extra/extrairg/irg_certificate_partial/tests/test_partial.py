# -*- coding: utf-8 -*-
from zipfile import ZipFile
from lxml import etree

from docx import Document as DocxDocument

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
        self._assert_bottom_right_arcs_are_visible_in_xml(res_file)
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
        expected_id_label = 'DNI/Pasaporte'
        if 'l10n_latam_identification_type_id' in self.partner._fields:
            identification_type = self.partner.l10n_latam_identification_type_id
            if identification_type:
                expected_id_label = identification_type.name
        self.assertIn(
            'Que Test Student Partial con %s  consta matriculado/a en '
            'el Test Course Partial durante el período académico' % expected_id_label,
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

        # Verificar que la firma (el dibujo) existe en el cuerpo en un párrafo vacío (inline)
        has_signature_drawing = False
        for p in document.paragraphs:
            drawings = p._element.xpath('.//w:drawing')
            if drawings and not p.text.strip():
                has_signature_drawing = True
                break
        self.assertTrue(
            has_signature_drawing,
            "La firma del departamento académico no se encuentra en un párrafo independiente vacío en el documento final."
        )

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

    def test_06_partial_gradebook_uses_partner_identification_type_name(self):
        """Partial gradebook must print the exact partner identification type."""
        if 'l10n_latam_identification_type_id' not in self.partner._fields:
            self.skipTest('l10n_latam identification type field is not available.')

        identification_type = self.env.ref(
            'l10n_latam_base.it_vat', raise_if_not_found=False
        )
        if not identification_type:
            identification_type = self.env['l10n_latam.identification.type'].create({
                'name': 'VAT',
            })
        self.partner.with_context(no_vat_validation=True).write({
            'l10n_latam_identification_type_id': identification_type.id,
            'vat': 'ID-123456',
        })
        cert = self.env['irg.certificate.request'].create({
            'gradebook_student_id': self.gradebook.id,
            'document_type': 'gradebook_partial',
            'certificate_type': 'digital',
            'state': 'draft',
        })

        res_file = cert._fill_template()
        document = DocxDocument(res_file)
        paragraph_text = '\n'.join(para.text for para in document.paragraphs)

        self.assertIn('%s ID-123456' % identification_type.name, paragraph_text)

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

    def test_07_partial_physical_omits_logo_and_arcs(self):
        """Physical/apostilled partial gradebook certificates must omit the header logo and decorative arcs."""
        for cert_type in ('physical', 'physical_apostilled'):
            cert = self.env['irg.certificate.request'].create({
                'gradebook_student_id': self.gradebook.id,
                'document_type': 'gradebook_partial',
                'certificate_type': cert_type,
                'shipping_type': 'national',
                'state': 'draft',
            })
            res_file = cert._fill_template()
            self._assert_bottom_right_arcs_are_absent_in_xml(res_file)
            self._assert_header_logo_is_removed_in_xml(res_file)

    def test_08_partial_non_physical_retains_logo_and_arcs(self):
        """Digital/custom partial gradebook certificates must retain the header logo and decorative arcs."""
        for cert_type in ('digital', 'custom'):
            cert = self.env['irg.certificate.request'].create({
                'gradebook_student_id': self.gradebook.id,
                'document_type': 'gradebook_partial',
                'certificate_type': cert_type,
                'state': 'draft',
            })
            res_file = cert._fill_template()
            self._assert_bottom_right_arcs_are_visible_in_xml(res_file)
            self._assert_header_logo_is_present_in_xml(res_file)

