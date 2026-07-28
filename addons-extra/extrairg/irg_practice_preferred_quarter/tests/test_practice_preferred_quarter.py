# -*- coding: utf-8 -*-

from odoo.addons.irg_practice_preferred_quarter.controllers.main import (
    IrgPracticePreferredQuarter,
)
from odoo.tests.common import TransactionCase


class TestPracticePreferredQuarter(TransactionCase):

    def test_preferred_quarter_field_exists_and_has_correct_selection(self):
        request_fields = self.env['practice.request']._fields

        self.assertIn('irg_preferred_quarter', request_fields)
        selection_dict = dict(request_fields['irg_preferred_quarter'].selection)
        self.assertEqual(
            selection_dict,
            {
                'marzo_mayo': 'Marzo a Mayo',
                'junio_agosto': 'Junio a Agosto',
                'septiembre_noviembre': 'Septiembre a Noviembre',
                'diciembre_febrero': 'Diciembre a Febrero',
            },
        )

    def test_allowed_quarters_in_controller(self):
        self.assertEqual(
            tuple(IrgPracticePreferredQuarter.ALLOWED_QUARTERS),
            (
                'marzo_mayo',
                'junio_agosto',
                'septiembre_noviembre',
                'diciembre_febrero',
            ),
        )

    def test_create_practice_request_saves_preferred_quarter(self):
        course = self.env['op.course'].create({
            'name': 'Curso Test Trimestre',
            'code': 'IRG-TRIM',
        })
        student_course = self.env['op.student.course'].create({
            'course_id': course.id,
        })
        practice_type = self.env['practice.center.type'].create({
            'type_of_practice': 'on_site',
        })

        practice_request = self.env['practice.request'].create({
            'name': 'Alumno Trimestre Test',
            'email': 'alumno.trimestre@example.com',
            'course_id': student_course.id,
            'practice_center_type_id': practice_type.id,
            'irg_preferred_quarter': 'marzo_mayo',
        })

        self.assertEqual(practice_request.irg_preferred_quarter, 'marzo_mayo')
