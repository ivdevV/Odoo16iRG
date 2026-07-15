# -*- coding: utf-8 -*-
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDiplomaTemplateWeighting(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course_index = 0
        cls.Product = cls.env['product.product']
        cls.CourseType = cls.env['op.course.type']
        cls.Course = cls.env['op.course']
        cls.Subject = cls.env['op.subject']
        cls.AdmissionRegister = cls.env['op.admission.register']
        cls.Admission = cls.env['op.admission']
        cls.Gradebook = cls.env['app.gradebook']
        cls.GradebookStudent = cls.env['app.gradebook.student']
        cls.GradebookSubject = cls.env['app.gradebook.subject']
        cls.GradebookResult = cls.env['app.gradebook.result']

        cls.registration_product = cls.Product.create({
            'name': 'IRG Template Weighting Registration',
            'type': 'service',
        })
        cls.diploma_type = cls.CourseType.create({
            'name': 'Diplomado',
            'code': 'DI',
        })
        cls.master_type = cls.CourseType.create({
            'name': 'Master',
            'code': 'M',
        })
        cls.special_template = cls.env.ref(
            'irg_diploma_gradebook_template_weighting.'
            'gradebook_diploma_exam_50_50'
        )
        cls.standard_template = cls.Gradebook.create({
            'name': 'Solo Examen',
            'final_calculation_mode': 'standard',
            'gradebook_template_ids': [(0, 0, {
                'type': 'exam',
                'weight': 100.0,
                'qty': 1,
            })],
        })

    def _create_course(self, name, course_type=None, **extra_values):
        type(self).course_index += 1
        values = {
            'name': name,
            'code': 'IRGDTW%03d' % type(self).course_index,
            'course_type_id': course_type.id if course_type else False,
        }
        values.update(extra_values)
        return self.Course.create(values)

    def _create_gradebook(self, course, template=None):
        partner = self.env['res.partner'].create({
            'name': 'IRG Template Weighting Student',
        })
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'IRG',
            'last_name': 'Student',
            'gender': 'm',
        })
        register = self.AdmissionRegister.create({
            'name': 'IRG Template Weighting Register',
            'course_id': course.id,
            'start_date': fields.Date.today(),
            'end_date': fields.Date.today(),
            'min_count': 1,
            'max_count': 100,
            'product_id': self.registration_product.id,
        })
        admission = self.Admission.create({
            'name': 'IRG Template Weighting Admission',
            'first_name': 'IRG',
            'last_name': 'Student',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'irg.template.weighting@example.com',
            'partner_id': partner.id,
            'student_id': student.id,
            'course_id': course.id,
            'register_id': register.id,
        })
        gradebook = self.GradebookStudent.create({
            'admission_id': admission.id,
        })
        gradebook.write({
            'gradebook_id': (template or self.special_template).id,
        })
        return gradebook

    def _add_subject_note(
        self, gradebook, subject_name, note, subject_type='compulsory'
    ):
        subject_index = len(gradebook.gradebook_subject_ids) + 1
        subject = self.Subject.create({
            'name': subject_name,
            'code': 'IRGDTW-%s-%s' % (gradebook.id, subject_index),
            'subject_type': subject_type,
            'course_id': gradebook.course_id.id,
        })
        line = self.GradebookSubject.create({
            'gradebook_student_id': gradebook.id,
            'op_subject_id': subject.id,
        })
        result = self.GradebookResult.create({
            'gradebook_subject_id': line.id,
            'survey_type': 'exam',
            'scoring_total': note,
        })
        return line, result

    def _build_gradebook(
        self,
        course_type,
        presencial_name='Modulo Presencial',
        presencial_note=10.0,
        module_notes=None,
        template=None,
        course_name='Diplomado en Neuroeducacion',
    ):
        course = self._create_course(course_name, course_type)
        gradebook = self._create_gradebook(course, template=template)
        if presencial_name is not None:
            self._add_subject_note(
                gradebook, presencial_name, presencial_note
            )
        ordinary_lines = []
        for index, note in enumerate(module_notes or [], 1):
            ordinary_lines.append(self._add_subject_note(
                gradebook, 'Modulo ordinario %s' % index, note
            ))
        self.env.flush_all()
        gradebook.invalidate_recordset()
        return gradebook, ordinary_lines

    def test_template_is_selectable_exam_100_and_special_mode(self):
        self.assertEqual(
            self.special_template.name,
            'Diplomado - Solo examen - Ponderación 50/50',
        )
        self.assertEqual(
            self.special_template.final_calculation_mode,
            'diploma_50_50',
        )
        self.assertEqual(len(self.special_template.gradebook_template_ids), 1)
        line = self.special_template.gradebook_template_ids
        self.assertEqual(line.type, 'exam')
        self.assertEqual(line.weight, 100.0)
        self.assertEqual(line.qty, 1)

    def test_real_presential_suffix_is_normalized(self):
        gradebook, _lines = self._build_gradebook(
            self.diploma_type,
            presencial_name=(
                'Diplomado en Neuroeducacion - MODULO PRESENCIAL/HOMECLASS'
            ),
            presencial_note=8.0,
            module_notes=[10.0, 10.0],
        )

        self.assertAlmostEqual(gradebook.total_final, 9.0)
        self.assertAlmostEqual(gradebook.avg_score, 9.0)

    def test_seven_modules_share_exactly_half_without_rounded_weights(self):
        gradebook, _lines = self._build_gradebook(
            self.diploma_type,
            presencial_name=(
                'Diplomado en Neuroeducacion - MODULO PRESENCIAL'
            ),
            presencial_note=8.0,
            module_notes=[10.0] * 7,
        )

        values = gradebook._get_diploma_weighting_values()
        self.assertEqual(values['non_presential_count'], 7)
        self.assertAlmostEqual(values['non_presential_weight'], 50.0 / 7.0)
        self.assertAlmostEqual(values['base_final'], 9.0)

    def test_distinct_notes_use_50_50_not_simple_average(self):
        gradebook, _lines = self._build_gradebook(
            self.diploma_type,
            presencial_note=4.0,
            module_notes=[10.0, 10.0, 10.0],
        )

        self.assertAlmostEqual(gradebook.total_final, 7.0)
        self.assertNotAlmostEqual(gradebook.total_final, 8.5)

    def test_variable_ordinary_module_counts(self):
        for count in (3, 6, 7):
            gradebook, _lines = self._build_gradebook(
                self.diploma_type,
                presencial_note=8.44,
                module_notes=[10.0] * count,
            )
            self.assertAlmostEqual(gradebook.total_final, 9.22)

    def test_non_diplomado_keeps_standard_average(self):
        gradebook, _lines = self._build_gradebook(
            self.master_type,
            presencial_note=8.0,
            module_notes=[10.0, 6.0],
            course_name='Master en Neuroeducacion',
        )

        self.assertAlmostEqual(gradebook.total_final, 8.0)
        self.assertAlmostEqual(gradebook.avg_score, 8.0)

    def test_diplomado_without_presential_keeps_standard_average(self):
        gradebook, _lines = self._build_gradebook(
            self.diploma_type,
            presencial_name=None,
            module_notes=[10.0, 8.0, 6.0],
        )

        self.assertAlmostEqual(gradebook.total_final, 8.0)

    def test_two_presential_candidates_keep_standard_average(self):
        gradebook, _lines = self._build_gradebook(
            self.diploma_type,
            presencial_note=10.0,
            module_notes=[6.0, 8.0],
        )
        self._add_subject_note(
            gradebook,
            'Diplomado en Neuroeducacion - Modulo Presencial',
            4.0,
        )
        self.env.flush_all()
        gradebook.invalidate_recordset()

        self.assertAlmostEqual(gradebook.total_final, 7.0)
        self.assertFalse(gradebook._get_diploma_weighting_values())

    def test_non_compulsory_subject_is_excluded(self):
        gradebook, _lines = self._build_gradebook(
            self.diploma_type,
            presencial_note=8.0,
            module_notes=[10.0, 10.0],
        )
        self._add_subject_note(
            gradebook,
            'Modulo optativo',
            0.0,
            subject_type='elective',
        )
        self.env.flush_all()
        gradebook.invalidate_recordset()

        self.assertAlmostEqual(gradebook.total_final, 9.0)

    def test_recomputes_after_note_name_type_and_template_changes(self):
        gradebook, ordinary_lines = self._build_gradebook(
            self.diploma_type,
            presencial_note=8.0,
            module_notes=[10.0, 10.0],
        )
        _ordinary_line, result = ordinary_lines[0]
        self.assertAlmostEqual(gradebook.total_final, 9.0)

        result.write({'scoring_total': 4.0})
        self.env.flush_all()
        gradebook.invalidate_recordset()
        self.assertAlmostEqual(gradebook.total_final, 7.5)

        gradebook.gradebook_subject_ids[0].op_subject_id.write({
            'name': 'Modulo renombrado',
        })
        self.env.flush_all()
        gradebook.invalidate_recordset()
        self.assertAlmostEqual(gradebook.total_final, 22.0 / 3.0)

        gradebook.gradebook_subject_ids[0].op_subject_id.write({
            'name': 'Modulo Presencial',
        })
        self.env.flush_all()
        gradebook.invalidate_recordset()
        self.assertAlmostEqual(gradebook.total_final, 7.5)

        gradebook.write({'gradebook_id': self.standard_template.id})
        self.env.flush_all()
        gradebook.invalidate_recordset()
        self.assertAlmostEqual(gradebook.total_final, 22.0 / 3.0)

    def test_recomputes_when_course_type_changes(self):
        gradebook, _lines = self._build_gradebook(
            self.diploma_type,
            presencial_note=4.0,
            module_notes=[10.0, 10.0, 10.0],
        )
        self.assertAlmostEqual(gradebook.total_final, 7.0)

        gradebook.course_id.write({'course_type_id': self.master_type.id})
        self.env.flush_all()
        gradebook.invalidate_recordset()

        self.assertAlmostEqual(gradebook.total_final, 8.5)

    def test_existing_solo_examen_template_stays_standard(self):
        gradebook, _lines = self._build_gradebook(
            self.diploma_type,
            presencial_note=4.0,
            module_notes=[10.0, 10.0, 10.0],
            template=self.standard_template,
        )

        self.assertEqual(
            self.standard_template.final_calculation_mode,
            'standard',
        )
        self.assertAlmostEqual(gradebook.total_final, 8.5)

    def test_category_identifies_diplomado_when_course_type_is_empty(self):
        category = self.env['product.category'].create({
            'name': 'Diplomado',
            'code': 'D',
        })
        product = self.env['product.template'].create({
            'name': 'Producto academico',
            'categ_id': category.id,
        })
        course = self._create_course(
            'Programa de Neuroeducacion',
            product_template_id=product.id,
        )
        gradebook = self._create_gradebook(course)
        self._add_subject_note(gradebook, 'Modulo Presencial', 8.0)
        self._add_subject_note(gradebook, 'Modulo ordinario', 10.0)
        self.env.flush_all()
        gradebook.invalidate_recordset()

        self.assertAlmostEqual(gradebook.total_final, 9.0)

        inconsistent_course = self._create_course(
            'Programa de Neuroeducacion con tipo inconsistente',
            self.master_type,
            product_template_id=product.id,
        )
        inconsistent_gradebook = self._create_gradebook(
            inconsistent_course
        )
        self._add_subject_note(
            inconsistent_gradebook, 'Modulo Presencial', 8.0
        )
        self._add_subject_note(
            inconsistent_gradebook, 'Modulo ordinario', 10.0
        )
        self.env.flush_all()
        inconsistent_gradebook.invalidate_recordset()

        self.assertAlmostEqual(inconsistent_gradebook.total_final, 9.0)

    def test_non_diploma_category_is_authoritative_over_course_name(self):
        category = self.env['product.category'].create({
            'name': 'Master',
            'code': 'M',
        })
        product = self.env['product.template'].create({
            'name': 'Producto academico de master',
            'categ_id': category.id,
        })
        course = self._create_course(
            'Diplomado en Neuroeducacion',
            product_template_id=product.id,
        )
        gradebook = self._create_gradebook(course)
        self._add_subject_note(gradebook, 'Modulo Presencial', 4.0)
        for index in range(3):
            self._add_subject_note(
                gradebook,
                'Modulo ordinario %s' % index,
                10.0,
            )
        self.env.flush_all()
        gradebook.invalidate_recordset()

        self.assertFalse(gradebook._get_diploma_weighting_values())
        self.assertAlmostEqual(gradebook.total_final, 8.5)

    def test_course_name_is_conservative_fallback(self):
        diploma_course = self._create_course('Diplomado en Neuroeducacion')
        diploma_gradebook = self._create_gradebook(diploma_course)
        self._add_subject_note(diploma_gradebook, 'Modulo Presencial', 8.0)
        self._add_subject_note(diploma_gradebook, 'Modulo ordinario', 10.0)

        other_course = self._create_course('Curso sobre diplomados')
        other_gradebook = self._create_gradebook(other_course)
        self._add_subject_note(other_gradebook, 'Modulo Presencial', 8.0)
        self._add_subject_note(other_gradebook, 'Modulo ordinario', 10.0)
        self.env.flush_all()
        diploma_gradebook.invalidate_recordset()
        other_gradebook.invalidate_recordset()

        self.assertAlmostEqual(diploma_gradebook.total_final, 9.0)
        self.assertAlmostEqual(other_gradebook.total_final, 9.0)
        self.assertFalse(other_gradebook._get_diploma_weighting_values())

    def test_recovery_uses_special_mode_without_changing_its_contract(self):
        gradebook, _lines = self._build_gradebook(
            self.diploma_type,
            presencial_note=6.0,
            module_notes=[6.0, 6.0, 6.0],
        )

        self.assertTrue(gradebook.diploma_recovery_required)
        gradebook.write({'diploma_recovery_score': 6.5})
        self.env.flush_all()
        gradebook.invalidate_recordset()
        self.assertAlmostEqual(gradebook.total_final, 6.5)

    def test_production_regression_six_tens_and_8_44_is_9_22(self):
        gradebook, _lines = self._build_gradebook(
            self.diploma_type,
            presencial_name=(
                'Diplomado en Terapias - MODULO PRESENCIAL/HOMECLASS'
            ),
            presencial_note=8.44,
            module_notes=[10.0] * 6,
        )

        self.assertAlmostEqual(gradebook.total_final, 9.22)
        self.assertAlmostEqual(gradebook.avg_score, 9.22)
