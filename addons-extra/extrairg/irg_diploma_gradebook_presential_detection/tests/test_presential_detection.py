# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDiplomaPresentialDetection(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course_index = 0
        cls.registration_product = cls.env['product.product'].create({
            'name': 'IRG Presential Detection Registration',
            'type': 'service',
        })
        cls.special_template = cls.env.ref(
            'irg_diploma_gradebook_template_weighting.'
            'gradebook_diploma_exam_50_50'
        )

    def _create_gradebook(self):
        type(self).course_index += 1
        index = type(self).course_index
        course = self.env['op.course'].create({
            'name': 'Diplomado detector presencial %s' % index,
            'code': 'IRGDP%03d' % index,
        })
        partner = self.env['res.partner'].create({
            'name': 'IRG Presential Detection Student %s' % index,
        })
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'IRG',
            'last_name': 'Student',
            'gender': 'm',
        })
        register = self.env['op.admission.register'].create({
            'name': 'IRG Presential Detection Register %s' % index,
            'course_id': course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
            'product_id': self.registration_product.id,
        })
        admission = self.env['op.admission'].create({
            'name': 'IRG Presential Detection Admission %s' % index,
            'first_name': 'IRG',
            'last_name': 'Student',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'irg.presential.%s@example.com' % index,
            'partner_id': partner.id,
            'student_id': student.id,
            'course_id': course.id,
            'register_id': register.id,
        })
        gradebook = self.env['app.gradebook.student'].create({
            'admission_id': admission.id,
            'gradebook_id': self.special_template.id,
        })
        return gradebook

    def _add_exam_score(self, gradebook, name, code, score):
        subject = self.env['op.subject'].create({
            'name': name,
            'code': code,
            'subject_type': 'compulsory',
            'course_id': gradebook.course_id.id,
        })
        line = self.env['app.gradebook.subject'].create({
            'gradebook_student_id': gradebook.id,
            'op_subject_id': subject.id,
        })
        self.env['app.gradebook.result'].create({
            'gradebook_subject_id': line.id,
            'survey_type': 'exam',
            'scoring_total': score,
        })
        return line

    def _refresh(self, gradebook):
        self.env.flush_all()
        gradebook.invalidate_recordset()

    def test_internal_subject_name_accepts_prefix_and_suffix(self):
        gradebook = self._create_gradebook()
        line = self._add_exam_score(
            gradebook,
            'Certificacion - Modulo presencial / Homeclass - Convocatoria 2',
            'PRES01',
            8.44,
        )

        self.assertTrue(gradebook._is_presential_module_subject(line))

    def test_visible_line_name_is_checked_when_internal_name_does_not_match(self):
        gradebook = self._create_gradebook()
        line = self._add_exam_score(
            gradebook,
            'Certificacion final',
            'PRES02',
            8.44,
        )
        line.write({'name': 'AD003983 - Modulo presencial'})

        self.assertTrue(gradebook._is_presential_module_subject(line))

    def test_six_tens_and_presential_844_equal_922(self):
        gradebook = self._create_gradebook()
        self._add_exam_score(
            gradebook,
            'AD003983 - Modulo presencial - Certificacion',
            'PRES03',
            8.44,
        )
        for index in range(6):
            self._add_exam_score(
                gradebook,
                'Modulo ordinario %s' % (index + 1),
                'ORD%02d' % (index + 1),
                10.0,
            )
        self._refresh(gradebook)

        self.assertAlmostEqual(gradebook.total_final, 9.22)
        self.assertAlmostEqual(gradebook.avg_score, 9.22)

    def test_partial_phrase_does_not_match(self):
        gradebook = self._create_gradebook()
        for name in (
            'Modulo presencialidad',
            'Supermodulo presencial',
            'Modulo semi presencial',
        ):
            line = self._add_exam_score(gradebook, name, name[:8], 8.44)
            self.assertFalse(
                gradebook._is_presential_module_subject(line),
                name,
            )

    def test_two_candidates_keep_safe_fallback(self):
        gradebook = self._create_gradebook()
        self._add_exam_score(
            gradebook,
            'Modulo presencial - Convocatoria ordinaria',
            'PRES04',
            8.44,
        )
        self._add_exam_score(
            gradebook,
            'Certificacion: Modulo presencial extraordinario',
            'PRES05',
            7.0,
        )
        for index in range(6):
            self._add_exam_score(
                gradebook,
                'Asignatura ordinaria %s' % (index + 1),
                'SAFE%02d' % (index + 1),
                10.0,
            )
        self._refresh(gradebook)

        expected_average = (8.44 + 7.0 + 60.0) / 8
        self.assertFalse(gradebook._get_diploma_weighting_values())
        self.assertAlmostEqual(gradebook.total_final, expected_average)
        self.assertAlmostEqual(gradebook.avg_score, expected_average)
