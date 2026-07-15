# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBetaCourseDetection(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course_index = 0
        cls.registration_product = cls.env['product.product'].create({
            'name': 'IRG Beta Course Detection Registration',
            'type': 'service',
        })
        cls.non_diploma_category = cls.env['product.category'].create({
            'name': 'Formacion continua',
            'code': 'FC',
        })
        cls.non_diploma_product = cls.env['product.template'].create({
            'name': 'Producto con clasificacion heredada',
            'categ_id': cls.non_diploma_category.id,
        })
        cls.non_diploma_type = cls.env['op.course.type'].create({
            'name': 'Curso',
            'code': 'C',
        })
        cls.special_template = cls.env.ref(
            'irg_diploma_gradebook_template_weighting.'
            'gradebook_diploma_exam_50_50'
        )
        cls.standard_template = cls.env['app.gradebook'].create({
            'name': 'IRG Beta Standard Exam Template',
            'final_calculation_mode': 'standard',
            'gradebook_template_ids': [(0, 0, {
                'type': 'exam',
                'weight': 100.0,
                'qty': 1,
            })],
        })

    def _create_course(self, name):
        type(self).course_index += 1
        return self.env['op.course'].create({
            'name': name,
            'code': 'IRGBCD%03d' % type(self).course_index,
            'course_type_id': self.non_diploma_type.id,
            'product_template_id': self.non_diploma_product.id,
        })

    def _create_gradebook(self, course, template):
        partner = self.env['res.partner'].create({
            'name': 'IRG Beta Course Detection Student',
        })
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'IRG',
            'last_name': 'Student',
            'gender': 'm',
        })
        register = self.env['op.admission.register'].create({
            'name': 'IRG Beta Course Detection Register',
            'course_id': course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
            'product_id': self.registration_product.id,
        })
        admission = self.env['op.admission'].create({
            'name': 'IRG Beta Course Detection Admission',
            'first_name': 'IRG',
            'last_name': 'Student',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'irg.beta.course.detection@example.com',
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

    def _build_beta_like_gradebook(self, name, template):
        gradebook = self._create_gradebook(
            self._create_course(name),
            template,
        )
        self._add_exam_score(
            gradebook,
            'Modulo presencial',
            'PRES01',
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

    def test_beta_category_mismatch_uses_50_50(self):
        gradebook = self._build_beta_like_gradebook(
            'Diplomado en Terapias de Tercera Generacion',
            self.special_template,
        )

        self.assertTrue(gradebook._is_diplomado_course())
        self.assertAlmostEqual(gradebook.total_final, 9.22)
        self.assertAlmostEqual(gradebook.avg_score, 9.22)

    def test_switching_standard_to_special_template_recomputes(self):
        gradebook = self._build_beta_like_gradebook(
            'TG - Diplomado en Terapias de Tercera Generacion',
            self.standard_template,
        )
        self.assertAlmostEqual(gradebook.total_final, 9.78, places=2)

        gradebook.write({'gradebook_id': self.special_template.id})
        self._refresh(gradebook)

        self.assertAlmostEqual(gradebook.total_final, 9.22)
        self.assertAlmostEqual(gradebook.avg_score, 9.22)

    def test_non_diploma_course_keeps_standard_average(self):
        gradebook = self._build_beta_like_gradebook(
            'Curso en Terapias de Tercera Generacion',
            self.special_template,
        )

        self.assertFalse(gradebook._is_diplomado_course())
        self.assertAlmostEqual(gradebook.total_final, 9.78, places=2)
        self.assertAlmostEqual(gradebook.avg_score, 9.78, places=2)
