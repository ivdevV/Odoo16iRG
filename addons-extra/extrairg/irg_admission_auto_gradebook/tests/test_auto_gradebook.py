# -*- coding: utf-8 -*-
"""
Tests para irg_admission_auto_gradebook.

Estrategia: se mockea super().enroll_student() para aislar la lógica propia
del módulo (creación de libreta) sin necesitar el stack completo de
OpenEduCat (fees, subject.registration, etc.).
"""
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestAutoGradebook(TransactionCase):

    def setUp(self):
        super().setUp()

        # Producto de servicio necesario para el register (dominio: type=service)
        self.product = self.env['product.product'].sudo().create({
            'name': 'Curso Test AGBook',
            'type': 'service',
            'list_price': 1000.0,
        })

        # Curso con auto-creación habilitada (filtro: solo obligatorias)
        self.course = self.env['op.course'].sudo().create({
            'name': 'Test Auto Gradebook Course',
            'code': 'TAGC01',
            'auto_create_gradebook': True,
            'auto_gradebook_subject_filter': 'compulsory',
        })

        # Asignatura obligatoria del curso
        self.subject_compulsory = self.env['op.subject'].sudo().create({
            'name': 'Matemáticas Test',
            'code': 'MAT01',
            'subject_type': 'compulsory',
        })
        # Asociar al curso vía Many2many
        self.course.sudo().write({
            'subject_ids': [(4, self.subject_compulsory.id)],
        })

        # Asignatura electiva del curso
        self.subject_elective = self.env['op.subject'].sudo().create({
            'name': 'Optativa Test',
            'code': 'OPT01',
            'subject_type': 'elective',
        })
        self.course.sudo().write({
            'subject_ids': [(4, self.subject_elective.id)],
        })

        # Admission register mínimo
        self.register = self.env['op.admission.register'].sudo().create({
            'name': 'Registro Test AGBook',
            'course_id': self.course.id,
            'product_id': self.product.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'state': 'admission',
        })

        # Admisión en estado pre-enroll (se forzará 'done' en cada test)
        self.admission = self.env['op.admission'].sudo().create({
            'first_name': 'Alumno',
            'name': 'Alumno Test Libreta',
            'last_name': 'Apellido Test',
            'register_id': self.register.id,
            'course_id': self.course.id,
            'application_date': '2026-04-01',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'alumno.test@example.com',
            'state': 'confirm',
            'mobile': '600000001',
        })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _simulate_enroll(self, admission):
        """Pone la admisión en estado 'done' y ejecuta el override del módulo
        sin invocar enroll_student() del super (que requiere stack completo)."""
        admission.sudo().write({'state': 'done'})
        # Llamamos directamente al código del override omitiendo super()
        with patch(
            'odoo.addons.openeducat_admission.models.admission'
            '.OpAdmission.enroll_student'
        ):
            admission.sudo().enroll_student()

    # ------------------------------------------------------------------
    # Tests
    # ------------------------------------------------------------------

    def test_gradebook_created_on_enroll(self):
        """Al confirmar la matrícula se debe crear exactamente 1 libreta."""
        self._simulate_enroll(self.admission)
        gradebooks = self.env['app.gradebook.student'].sudo().search([
            ('admission_id', '=', self.admission.id),
        ])
        self.assertEqual(
            len(gradebooks), 1,
            'Debe haberse creado exactamente 1 libreta para la admisión.',
        )

    def test_subjects_compulsory_filter(self):
        """Con filtro 'compulsory' solo se añaden las asignaturas obligatorias."""
        self._simulate_enroll(self.admission)
        gradebook = self.env['app.gradebook.student'].sudo().search([
            ('admission_id', '=', self.admission.id),
        ], limit=1)
        subject_ids = gradebook.gradebook_subject_ids.mapped('op_subject_id').ids
        self.assertIn(
            self.subject_compulsory.id, subject_ids,
            'La asignatura obligatoria debe estar en la libreta.',
        )
        self.assertNotIn(
            self.subject_elective.id, subject_ids,
            'La asignatura electiva NO debe estar con el filtro "compulsory".',
        )

    def test_subjects_all_filter(self):
        """Con filtro 'all' se deben añadir todas las asignaturas del curso."""
        self.course.sudo().write({'auto_gradebook_subject_filter': 'all'})
        self._simulate_enroll(self.admission)
        gradebook = self.env['app.gradebook.student'].sudo().search([
            ('admission_id', '=', self.admission.id),
        ], limit=1)
        subject_ids = gradebook.gradebook_subject_ids.mapped('op_subject_id').ids
        self.assertIn(self.subject_compulsory.id, subject_ids)
        self.assertIn(self.subject_elective.id, subject_ids)

    def test_no_duplicate_gradebook(self):
        """Llamar enroll_student dos veces no debe crear una segunda libreta."""
        self._simulate_enroll(self.admission)
        self._simulate_enroll(self.admission)
        gradebooks = self.env['app.gradebook.student'].sudo().search([
            ('admission_id', '=', self.admission.id),
        ])
        self.assertEqual(
            len(gradebooks), 1,
            'No deben crearse libretas duplicadas para la misma admisión.',
        )

    def test_disabled_course_no_gradebook(self):
        """Si auto_create_gradebook=False no se debe crear ninguna libreta."""
        self.course.sudo().write({'auto_create_gradebook': False})
        self._simulate_enroll(self.admission)
        gradebooks = self.env['app.gradebook.student'].sudo().search([
            ('admission_id', '=', self.admission.id),
        ])
        self.assertEqual(
            len(gradebooks), 0,
            'No debe crearse libreta cuando auto_create_gradebook está desactivado.',
        )
