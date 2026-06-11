# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.addons.irg_practice_request_student_profile.controllers.main import (
    IrgPracticeRequestStudentProfile,
)
from odoo.tests.common import TransactionCase


class TestPracticeRequestStudentProfile(TransactionCase):

    def test_student_profile_fields_exist(self):
        request_fields = self.env['practice.request']._fields

        self.assertIn('irg_age', request_fields)
        self.assertIn('irg_current_job_related_to_master', request_fields)
        self.assertEqual(
            dict(request_fields['irg_current_job_related_to_master'].selection),
            {'yes': 'Sí', 'no': 'No', 'partial': 'Parcialmente'},
        )

    def test_all_student_profile_fields_are_required_in_portal_controller(self):
        self.assertEqual(
            set(IrgPracticeRequestStudentProfile._required_profile_fields),
            {
                'irg_age',
                'irg_academic_degrees',
                'irg_postgraduate_training',
                'irg_related_work_experience',
                'irg_currently_working',
                'irg_current_job_related_to_master',
                'irg_master_motivation',
                'irg_master_expectations',
                'irg_long_term_professional_goals',
                'irg_topics_to_deepen',
                'irg_future_training_interest',
            },
        )

    def test_create_stores_student_profile_values(self):
        today = fields.Date.today()
        course = self.env['op.course'].create({
            'name': 'Curso test perfil alumno',
            'code': 'IRG-PRF',
        })
        batch = self.env['op.batch'].create({
            'name': 'Batch perfil alumno',
            'code': 'IRG-PRF-B',
            'course_id': course.id,
            'start_date': today,
            'end_date': today + relativedelta(months=1),
        })
        student_course = self.env['op.student.course'].create({
            'course_id': course.id,
            'batch_id': batch.id,
        })
        practice_type = self.env['practice.center.type'].create({
            'type_of_practice': 'on_site',
        })

        practice_request = self.env['practice.request'].create({
            'name': 'Alumno Test',
            'email': 'alumno.test@example.com',
            'course_id': student_course.id,
            'practice_center_type_id': practice_type.id,
            'irg_age': 31,
            'irg_academic_degrees': 'Licenciatura, Universidad Test, 2018',
            'irg_current_job_related_to_master': 'partial',
            'irg_master_motivation': 'Mejorar competencias profesionales',
        })

        self.assertEqual(practice_request.irg_age, 31)
        self.assertEqual(
            practice_request.irg_academic_degrees,
            'Licenciatura, Universidad Test, 2018',
        )
        self.assertEqual(practice_request.irg_current_job_related_to_master, 'partial')
        self.assertEqual(
            practice_request.irg_master_motivation,
            'Mejorar competencias profesionales',
        )
