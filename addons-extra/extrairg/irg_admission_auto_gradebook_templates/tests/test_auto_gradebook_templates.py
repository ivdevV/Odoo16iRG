# -*- coding: utf-8 -*-
"""Tests for irg_admission_auto_gradebook_templates."""
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'irg_admission_auto_gradebook_templates')
class TestAutoGradebookTemplates(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env['product.product'].sudo().create({
            'name': 'Curso Test AG Templates',
            'type': 'service',
            'list_price': 1000.0,
        })
        self.course_template = self.env['app.gradebook'].sudo().create({
            'name': 'Template Curso Custom AG',
            'gradebook_template_ids': [(0, 0, {
                'type': 'exam',
                'weight': 100.0,
                'qty': 1,
            })],
        })
        self.diploma_template = self.env.ref(
            'irg_diploma_gradebook_template_weighting.gradebook_diploma_exam_50_50'
        )
        self.solo_examen = self.env.ref(
            'irg_admission_auto_gradebook_templates.gradebook_master_solo_examen'
        )

    def _create_course(self, name, code, **extra):
        vals = {
            'name': name,
            'code': code,
            'lang': self.env.user.lang or 'en_US',
            'auto_create_gradebook': True,
            'auto_gradebook_subject_filter': 'compulsory',
        }
        vals.update(extra)
        course = self.env['op.course'].sudo().create(vals)
        subject = self.env['op.subject'].sudo().create({
            'name': 'Asignatura %s' % code,
            'code': 'SUB-%s' % code,
            'subject_type': 'compulsory',
        })
        course.sudo().write({'subject_ids': [(4, subject.id)]})
        return course, subject

    def _create_admission(self, course, suffix):
        register = self.env['op.admission.register'].sudo().create({
            'name': 'Registro AG Templates %s' % suffix,
            'course_id': course.id,
            'product_id': self.product.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'state': 'admission',
            'min_count': 1,
            'max_count': 100,
        })
        return self.env['op.admission'].sudo().create({
            'first_name': 'Alumno',
            'name': 'Alumno AG Templates %s' % suffix,
            'last_name': 'Apellido',
            'register_id': register.id,
            'course_id': course.id,
            'application_date': '2026-04-01',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'ag.templates.%s@example.com' % suffix.lower(),
            'state': 'done',
            'mobile': '600000099',
        })

    def _create_auto_gradebook(self, admission):
        """Reproduce irg_admission_auto_gradebook without OpenEduCat enroll stack."""
        course = admission.course_id
        gradebook = self.env['app.gradebook.student'].sudo().create({
            'admission_id': admission.id,
        })
        subjects = course.subject_ids
        if course.auto_gradebook_subject_filter == 'compulsory':
            subjects = subjects.filtered(lambda s: s.subject_type == 'compulsory')
        for subject in subjects:
            self.env['app.gradebook.subject'].sudo().create({
                'gradebook_student_id': gradebook.id,
                'op_subject_id': subject.id,
            })
        return gradebook

    def _apply_templates(self, admission):
        admission._irg_assign_auto_gradebook_templates()

    def test_course_template_takes_precedence(self):
        course, _subject = self._create_course(
            'Curso con template propio',
            'AGTCOURSE',
            gradebook_id=self.course_template.id,
        )
        admission = self._create_admission(course, '01')
        gradebook = self._create_auto_gradebook(admission)
        self._apply_templates(admission)
        self.assertEqual(gradebook.gradebook_id, self.course_template)

    def test_diplomado_gets_canonical_template(self):
        course_type = self.env['op.course.type'].sudo().create({
            'name': 'Diplomado',
            'code': 'DIPAGT',
        })
        course, _subject = self._create_course(
            'Formación Continua Genérica',
            'AGTDIP01',
            course_type_id=course_type.id,
        )
        admission = self._create_admission(course, '02')
        gradebook = self._create_auto_gradebook(admission)
        self.assertFalse(gradebook.gradebook_id)
        self._apply_templates(admission)
        self.assertEqual(gradebook.gradebook_id, self.diploma_template)

    def test_master_by_course_type_gets_solo_examen(self):
        course_type = self.env['op.course.type'].sudo().create({
            'name': 'Máster',
            'code': 'MSTAGT',
        })
        course, _subject = self._create_course(
            'Programa Avanzado',
            'AGTMST01',
            course_type_id=course_type.id,
        )
        admission = self._create_admission(course, '03')
        gradebook = self._create_auto_gradebook(admission)
        self.assertFalse(gradebook.gradebook_id)
        self._apply_templates(admission)
        self.assertEqual(gradebook.gradebook_id, self.solo_examen)

    def test_master_by_course_name_gets_solo_examen(self):
        course, _subject = self._create_course(
            'Máster en Evaluación Neuropsicológica',
            'AGTMST02',
        )
        admission = self._create_admission(course, '04')
        gradebook = self._create_auto_gradebook(admission)
        self.assertFalse(gradebook.gradebook_id)
        self._apply_templates(admission)
        self.assertEqual(gradebook.gradebook_id, self.solo_examen)

    def test_other_course_without_template_stays_empty(self):
        course, _subject = self._create_course(
            'Taller de Actualización',
            'AGTOTH01',
        )
        admission = self._create_admission(course, '05')
        gradebook = self._create_auto_gradebook(admission)
        self._apply_templates(admission)
        self.assertFalse(gradebook.gradebook_id)

    def test_subject_lines_not_force_written(self):
        course, subject = self._create_course(
            'Master HC Subject Check',
            'AGTMST03',
        )
        admission = self._create_admission(course, '06')
        gradebook = self._create_auto_gradebook(admission)
        self._apply_templates(admission)
        self.assertEqual(gradebook.gradebook_id, self.solo_examen)
        line = gradebook.gradebook_subject_ids.filtered(
            lambda r: r.op_subject_id == subject
        )
        self.assertTrue(line)
        self.assertFalse(line.gradebook_id)
