# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDiplomaTemplateAuthoritative(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course_index = 0
        cls.registration_product = cls.env['product.product'].create({
            'name': 'IRG Authoritative Gradebook Registration',
            'type': 'service',
        })
        cls.special_template = cls.env.ref(
            'irg_diploma_gradebook_template_weighting.'
            'gradebook_diploma_exam_50_50'
        )
        cls.standard_template = cls.env['app.gradebook'].create({
            'name': 'IRG Authoritative Standard Exam Template',
            'final_calculation_mode': 'standard',
            'gradebook_template_ids': [(0, 0, {
                'type': 'exam',
                'weight': 100.0,
                'qty': 1,
            })],
        })

    def _create_gradebook(self, template):
        type(self).course_index += 1
        index = type(self).course_index
        course = self.env['op.course'].create({
            'name': 'Curso ordinario autoritativo %s' % index,
            'code': 'IRGAT%03d' % index,
        })
        partner = self.env['res.partner'].create({
            'name': 'IRG Authoritative Student %s' % index,
        })
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'IRG',
            'last_name': 'Student',
            'gender': 'm',
        })
        register = self.env['op.admission.register'].create({
            'name': 'IRG Authoritative Register %s' % index,
            'course_id': course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
            'product_id': self.registration_product.id,
        })
        admission = self.env['op.admission'].create({
            'name': 'IRG Authoritative Admission %s' % index,
            'first_name': 'IRG',
            'last_name': 'Student',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'irg.authoritative.%s@example.com' % index,
            'partner_id': partner.id,
            'student_id': student.id,
            'course_id': course.id,
            'register_id': register.id,
        })
        gradebook = self.env['app.gradebook.student'].create({
            'admission_id': admission.id,
        })
        gradebook.write({'gradebook_id': template.id})
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

    def _build_gradebook(self, template, presencial_count=1):
        gradebook = self._create_gradebook(template)
        for index in range(presencial_count):
            self._add_exam_score(
                gradebook,
                'Modulo presencial',
                'PRES%02d' % (index + 1),
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
        return gradebook

    def _refresh(self, gradebook):
        self.env.flush_all()
        gradebook.invalidate_recordset()

    def test_special_template_is_authoritative_when_detector_is_false(self):
        gradebook = self._build_gradebook(self.special_template)

        with patch.object(
            type(gradebook),
            '_is_diplomado_course',
            return_value=False,
        ) as detector:
            gradebook._amount_prod_final()
            gradebook.compute_avg_score()

        detector.assert_not_called()
        self.assertAlmostEqual(gradebook.total_final, 9.22)
        self.assertAlmostEqual(gradebook.avg_score, 9.22)

    def test_switching_template_recomputes_immediately(self):
        gradebook = self._build_gradebook(self.standard_template)
        self.assertAlmostEqual(gradebook.total_final, 9.78, places=2)

        gradebook.write({'gradebook_id': self.special_template.id})

        self.assertAlmostEqual(gradebook.total_final, 9.22)
        self.assertAlmostEqual(gradebook.avg_score, 9.22)

    def test_standard_template_keeps_inherited_average(self):
        gradebook = self._build_gradebook(self.standard_template)

        self.assertAlmostEqual(gradebook.total_final, 9.78, places=2)
        self.assertAlmostEqual(gradebook.avg_score, 9.78, places=2)

    def test_nlex_subject_remains_excluded(self):
        gradebook = self._build_gradebook(self.special_template)
        self._add_exam_score(
            gradebook,
            'Asignatura NLEX excluida',
            'NLEX01',
            1.0,
        )
        self._refresh(gradebook)

        self.assertAlmostEqual(gradebook.total_final, 9.22)
        self.assertAlmostEqual(gradebook.avg_score, 9.22)

    def test_invalid_presential_count_falls_back_safely(self):
        gradebook = self._build_gradebook(
            self.special_template,
            presencial_count=2,
        )

        expected_average = ((8.44 * 2) + (10.0 * 6)) / 8
        self.assertFalse(gradebook._get_diploma_weighting_values())
        self.assertAlmostEqual(gradebook.total_final, expected_average)
        self.assertAlmostEqual(gradebook.avg_score, expected_average)
