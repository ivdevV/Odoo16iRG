# -*- coding: utf-8 -*-
"""
Tests para irg_gradebook_editable_template.

Verifican que gradebook_id en app.gradebook.student:
1. Es editable (readonly=False a nivel de campo).
2. Un valor puesto a mano sobrevive al recálculo aunque el curso no tenga template.
3. Se sigue rellenando solo desde el template del curso (comportamiento original).
"""
from odoo.tests.common import TransactionCase


class TestEditableTemplate(TransactionCase):

    def setUp(self):
        super().setUp()

        self.product = self.env['product.product'].sudo().create({
            'name': 'Curso Test Template Editable',
            'type': 'service',
            'list_price': 1000.0,
        })

        # Curso SIN template de calificaciones
        self.course = self.env['op.course'].sudo().create({
            'name': 'Test Editable Template Course',
            'code': 'TETC01',
            'lang': self.env.user.lang or 'en_US',
        })

        self.register = self.env['op.admission.register'].sudo().create({
            'name': 'Registro Test Template Editable',
            'course_id': self.course.id,
            'product_id': self.product.id,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'state': 'admission',
            'min_count': 1,
            'max_count': 100,
        })

        self.admission = self.env['op.admission'].sudo().create({
            'first_name': 'Alumno',
            'name': 'Alumno Test Template',
            'last_name': 'Apellido Test',
            'register_id': self.register.id,
            'course_id': self.course.id,
            'application_date': '2026-04-01',
            'birth_date': '2000-01-01',
            'gender': 'm',
            'email': 'alumno.template@example.com',
            'state': 'confirm',
            'mobile': '600000002',
        })

        # Constraint: total_percent debe sumar 100
        self.template = self.env['app.gradebook'].sudo().create({
            'name': 'Template Test Manual',
            'gradebook_template_ids': [(0, 0, {
                'type': 'exam',
                'weight': 100.0,
                'qty': 1,
            })],
        })

    def _create_gradebook(self):
        return self.env['app.gradebook.student'].sudo().create({
            'admission_id': self.admission.id,
        })

    def test_field_is_editable(self):
        """gradebook_id debe tener readonly=False para ser editable en vistas."""
        field = self.env['app.gradebook.student']._fields['gradebook_id']
        self.assertFalse(
            field.readonly,
            'gradebook_id debe ser editable (readonly=False).',
        )

    def test_manual_value_preserved_on_recompute(self):
        """Valor manual no debe perderse al recalcular si el curso no tiene template."""
        gradebook = self._create_gradebook()
        self.assertFalse(gradebook.gradebook_id, 'Curso sin template: campo vacío.')

        gradebook.sudo().write({'gradebook_id': self.template.id})
        # Forzar recálculo como haría cualquier cambio en course_id
        gradebook.sudo().compute_gradebook_id()

        self.assertEqual(
            gradebook.gradebook_id, self.template,
            'El template puesto a mano debe sobrevivir al recálculo.',
        )

    def test_course_template_fills_empty(self):
        """Si el curso tiene template y la libreta no, el compute lo rellena."""
        self.course.sudo().write({'gradebook_id': self.template.id})
        gradebook = self._create_gradebook()

        self.assertEqual(
            gradebook.gradebook_id, self.template,
            'El compute debe seguir copiando el template del curso.',
        )
