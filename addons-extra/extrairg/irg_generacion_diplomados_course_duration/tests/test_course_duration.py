# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'irg_generacion_diplomados_course_duration')
class TestDiplomadoCourseDuration(TransactionCase):
    def test_wizard_loads_course_hours_and_ects(self):
        course = self.env['op.course'].create({
            'name': 'Diplomado Duracion Test',
            'code': 'DIPDUR',
            'irg_diplomado_duration_hours': 125,
            'irg_diplomado_duration_ects': 5.5,
            'irg_diplomado_subjects_presencial': 'Asignatura presencial',
            'irg_diplomado_subjects_online': 'Asignatura online',
        })

        wizard = self.env['irg.diplomado.wizard'].new({'course_id': course.id})
        wizard._onchange_course_id()

        self.assertEqual(wizard.diplomado_name, course.name)
        self.assertEqual(wizard.duration_hours, 125)
        self.assertEqual(wizard.duration_ects, 5.5)
        self.assertEqual(wizard.subjects_presencial, 'Asignatura presencial')
        self.assertEqual(wizard.subjects_online, 'Asignatura online')
