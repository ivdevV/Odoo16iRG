# -*- coding: utf-8 -*-
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDiplomaGradebookWeighting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Product = cls.env['product.product']
        cls.CourseType = cls.env['op.course.type']
        cls.Course = cls.env['op.course']
        cls.Subject = cls.env['op.subject']
        cls.AdmissionRegister = cls.env['op.admission.register']
        cls.Admission = cls.env['op.admission']
        cls.GradebookStudent = cls.env['app.gradebook.student']
        cls.GradebookSubject = cls.env['app.gradebook.subject']
        cls.GradebookResult = cls.env['app.gradebook.result']

        cls.product = cls.Product.create({
            'name': 'IRG Diploma Weighting Product',
            'type': 'service',
        })
        cls.diploma_type = cls.CourseType.create({
            'name': 'Diplomado',
            'code': 'DIP',
        })
        cls.master_type = cls.CourseType.create({
            'name': 'Master',
            'code': 'MAS',
        })
        cls.course_index = 0

    def _create_course(self, name, course_type):
        type(self).course_index += 1
        return self.Course.create({
            'name': name,
            'code': 'IRGDGW%02d' % type(self).course_index,
            'course_type_id': course_type.id,
        })

    def _create_gradebook(self, course):
        partner = self.env['res.partner'].create({
            'name': 'IRG Diploma Weighting Student',
        })
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'IRG',
            'last_name': 'Student',
            'gender': 'm',
        })
        register = self.AdmissionRegister.create({
            'name': 'IRG Diploma Weighting Register',
            'course_id': course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
            'product_id': self.product.id,
        })
        admission = self.Admission.create({
            'name': 'IRG Diploma Weighting Admission',
            'first_name': 'IRG',
            'last_name': 'Student',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'irg.diploma.weighting@example.com',
            'partner_id': partner.id,
            'student_id': student.id,
            'course_id': course.id,
            'register_id': register.id,
        })
        return self.GradebookStudent.create({
            'admission_id': admission.id,
        })

    def _add_subject_note(self, gradebook, subject_name, note):
        subject_index = len(gradebook.gradebook_subject_ids) + 1
        subject = self.Subject.create({
            'name': subject_name,
            'code': 'IRGDGW-%s-%s' % (gradebook.id, subject_index),
            'subject_type': 'compulsory',
            'course_id': gradebook.course_id.id,
        })
        line = self.GradebookSubject.create({
            'gradebook_student_id': gradebook.id,
            'op_subject_id': subject.id,
        })
        self.GradebookResult.create({
            'gradebook_subject_id': line.id,
            'survey_type': 'exam',
            'scoring_total': note,
        })
        return line

    def _build_gradebook(self, course_type, presencial_note=None, module_notes=None):
        course = self._create_course(
            'IRG Diploma Weighting Course %s' % (type(self).course_index + 1),
            course_type,
        )
        gradebook = self._create_gradebook(course)
        if presencial_note is not None:
            self._add_subject_note(gradebook, 'Módulo Presencial', presencial_note)
        for index, note in enumerate(module_notes or [], 1):
            self._add_subject_note(gradebook, 'Modulo Online %s' % index, note)
        self.env.flush_all()
        gradebook.invalidate_recordset()
        return gradebook

    def test_diplomado_six_modules_uses_50_50_weighting(self):
        gradebook = self._build_gradebook(
            self.diploma_type,
            presencial_note=10.0,
            module_notes=[8.0, 8.0, 8.0, 8.0, 8.0, 8.0],
        )

        self.assertAlmostEqual(gradebook.total_final, 9.0)
        self.assertAlmostEqual(gradebook.avg_score, 9.0)

    def test_diplomado_any_module_count_keeps_non_presential_block_at_50(self):
        gradebook = self._build_gradebook(
            self.diploma_type,
            presencial_note=10.0,
            module_notes=[6.0, 8.0, 10.0],
        )

        self.assertAlmostEqual(gradebook.total_final, 9.0)
        self.assertAlmostEqual(gradebook.avg_score, 9.0)

    def test_non_diplomado_keeps_standard_simple_average(self):
        gradebook = self._build_gradebook(
            self.master_type,
            presencial_note=10.0,
            module_notes=[8.0, 6.0],
        )

        self.assertAlmostEqual(gradebook.total_final, 8.0)
        self.assertAlmostEqual(gradebook.avg_score, 8.0)

    def test_diplomado_without_presential_keeps_standard_simple_average(self):
        gradebook = self._build_gradebook(
            self.diploma_type,
            module_notes=[10.0, 8.0, 6.0],
        )

        self.assertAlmostEqual(gradebook.total_final, 8.0)
        self.assertAlmostEqual(gradebook.avg_score, 8.0)

    def test_diplomado_base_below_seven_requires_recovery(self):
        gradebook = self._build_gradebook(
            self.diploma_type,
            presencial_note=6.0,
            module_notes=[6.0, 6.0, 6.0],
        )

        self.assertTrue(gradebook.diploma_recovery_required)
        self.assertFalse(gradebook.diploma_recovery_applied)
        self.assertAlmostEqual(gradebook.total_final, 6.0)

    def test_recovery_score_replaces_final_and_validates_maximum(self):
        gradebook = self._build_gradebook(
            self.diploma_type,
            presencial_note=6.0,
            module_notes=[6.0, 6.0, 6.0],
        )

        gradebook.write({'diploma_recovery_score': 6.5})
        self.env.flush_all()
        gradebook.invalidate_recordset()

        self.assertTrue(gradebook.diploma_recovery_applied)
        self.assertAlmostEqual(gradebook.total_final, 6.5)
        self.assertAlmostEqual(gradebook.avg_score, 6.5)

        with self.assertRaises(ValidationError):
            gradebook.write({'diploma_recovery_score': 7.1})
