# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDiplomaTemplateNlexCompatibility(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course_index = 0
        cls.registration_product = cls.env['product.product'].create({
            'name': 'IRG Diploma NLEX Registration',
            'type': 'service',
        })
        cls.diploma_type = cls.env['op.course.type'].create({
            'name': 'Diplomado',
            'code': 'DI',
        })
        cls.master_type = cls.env['op.course.type'].create({
            'name': 'Master',
            'code': 'M',
        })
        cls.special_template = cls.env.ref(
            'irg_diploma_gradebook_template_weighting.'
            'gradebook_diploma_exam_50_50'
        )
        cls.standard_template = cls.env['app.gradebook'].create({
            'name': 'IRG NLEX Standard Template',
            'final_calculation_mode': 'standard',
            'gradebook_template_ids': [(0, 0, {
                'type': 'exam',
                'weight': 100.0,
                'qty': 1,
            })],
        })

    def _create_course(self, course_type, name):
        type(self).course_index += 1
        return self.env['op.course'].create({
            'name': name,
            'code': 'IRGDNX%03d' % type(self).course_index,
            'course_type_id': course_type.id,
        })

    def _create_gradebook(self, course, template):
        partner = self.env['res.partner'].create({
            'name': 'IRG Diploma NLEX Student',
        })
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'IRG',
            'last_name': 'Student',
            'gender': 'm',
        })
        register = self.env['op.admission.register'].create({
            'name': 'IRG Diploma NLEX Register',
            'course_id': course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
            'product_id': self.registration_product.id,
        })
        admission = self.env['op.admission'].create({
            'name': 'IRG Diploma NLEX Admission',
            'first_name': 'IRG',
            'last_name': 'Student',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'irg.diploma.nlex@example.com',
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

    def _add_note(self, gradebook, name, code, score):
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

    def test_special_diploma_keeps_9_22_with_nlex_installed(self):
        course = self._create_course(
            self.diploma_type, 'Diplomado en Terapias'
        )
        gradebook = self._create_gradebook(course, self.special_template)
        self._add_note(
            gradebook,
            'Diplomado en Terapias - MODULO PRESENCIAL/HOMECLASS',
            'PRES01',
            8.44,
        )
        for index in range(6):
            self._add_note(
                gradebook,
                'Modulo ordinario %s' % (index + 1),
                'ORD%02d' % (index + 1),
                10.0,
            )
        self._add_note(gradebook, 'Nivelacion NLEX', 'NLEX01', 0.0)
        self._refresh(gradebook)

        self.assertAlmostEqual(gradebook.total_final, 9.22)
        self.assertAlmostEqual(gradebook.avg_score, 9.22)

    def test_standard_template_keeps_inherited_nlex_average(self):
        course = self._create_course(
            self.diploma_type, 'Diplomado con template estandar'
        )
        gradebook = self._create_gradebook(course, self.standard_template)
        self._add_note(gradebook, 'Modulo Presencial', 'PRES02', 4.0)
        for index in range(3):
            self._add_note(
                gradebook,
                'Modulo ordinario %s' % (index + 1),
                'STD%02d' % (index + 1),
                10.0,
            )
        self._add_note(gradebook, 'Nivelacion NLEX', 'NLEX02', 0.0)
        self._refresh(gradebook)

        self.assertAlmostEqual(gradebook.total_final, 8.5)
        self.assertAlmostEqual(gradebook.avg_score, 8.5)

    def test_non_diploma_special_template_keeps_inherited_average(self):
        course = self._create_course(
            self.master_type, 'Master en Terapias'
        )
        gradebook = self._create_gradebook(course, self.special_template)
        self._add_note(gradebook, 'Modulo Presencial', 'PRES03', 4.0)
        for index in range(3):
            self._add_note(
                gradebook,
                'Modulo ordinario %s' % (index + 1),
                'MAS%02d' % (index + 1),
                10.0,
            )
        self._add_note(gradebook, 'Nivelacion NLEX', 'NLEX03', 0.0)
        self._refresh(gradebook)

        self.assertAlmostEqual(gradebook.total_final, 8.5)
        self.assertAlmostEqual(gradebook.avg_score, 8.5)

    def test_nlex_remains_excluded_from_special_ordinary_block(self):
        course = self._create_course(
            self.diploma_type, 'Diplomado con NLEX puntuado'
        )
        gradebook = self._create_gradebook(course, self.special_template)
        self._add_note(gradebook, 'Modulo Presencial', 'PRES04', 8.0)
        self._add_note(gradebook, 'Modulo ordinario', 'ORD99', 10.0)
        self._add_note(gradebook, 'Nivelacion NLEX', 'NLEX99', 2.0)
        self._refresh(gradebook)

        values = gradebook._get_diploma_weighting_values()
        self.assertEqual(values['non_presential_count'], 1)
        self.assertAlmostEqual(values['non_presential_average'], 10.0)
        self.assertAlmostEqual(gradebook.total_final, 9.0)
        self.assertAlmostEqual(gradebook.avg_score, 9.0)
