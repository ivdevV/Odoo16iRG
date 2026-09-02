# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from lxml import etree

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'irg_student_course_practice_modality')
class TestStudentCoursePracticeModality(TransactionCase):

    def _make_enrollment(self, suffix):
        today = fields.Date.today()
        course = self.env['op.course'].create({
            'name': 'Curso practicas %s' % suffix,
            'code': 'IRG-PM-%s' % suffix,
            'lang': self.env.user.lang or 'en_US',
        })
        batch = self.env['op.batch'].create({
            'name': 'Lote %s' % suffix,
            'code': 'IRG-PM-B-%s' % suffix,
            'course_id': course.id,
            'start_date': today,
            'end_date': today + relativedelta(months=1),
        })
        partner = self.env['res.partner'].create({
            'name': 'Alumno %s' % suffix,
            'email': 'alumno.%s@example.test' % suffix.lower(),
        })
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'Alumno',
            'last_name': suffix,
            'gender': 'o',
        })
        enrollment = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': course.id,
            'batch_id': batch.id,
        })
        return course, student, enrollment

    def _make_practice_type(self, type_of_practice):
        return self.env['practice.center.type'].create({
            'type_of_practice': type_of_practice,
        })

    def _make_request(self, enrollment, practice_type, state='draft'):
        return self.env['practice.request'].create({
            'name': enrollment.student_id.name,
            'email': enrollment.student_id.email or 'alumno@example.test',
            'course_id': enrollment.id,
            'practice_center_type_id': practice_type.id,
            'state': state,
        })

    def test_enrollment_field_exists(self):
        self.assertIn(
            'irg_practice_center_type_id',
            self.env['op.student.course']._fields,
        )

    def test_draft_request_does_not_sync(self):
        _course, _student, enrollment = self._make_enrollment('DRAFT')
        practice_type = self._make_practice_type('on_site')
        self._make_request(enrollment, practice_type, state='draft')
        self.assertFalse(enrollment.irg_practice_center_type_id)

    def test_approve_syncs_modality_to_enrollment(self):
        _course, _student, enrollment = self._make_enrollment('APPR')
        practice_type = self._make_practice_type('tfm_validation')
        request = self._make_request(enrollment, practice_type, state='draft')
        request.action_approve()
        self.assertEqual(enrollment.irg_practice_center_type_id, practice_type)

    def test_progress_and_end_keep_syncing(self):
        _course, _student, enrollment = self._make_enrollment('PROG')
        practice_type = self._make_practice_type('validation')
        request = self._make_request(enrollment, practice_type, state='draft')
        request.action_approve()
        request.write({'state': 'progress'})
        self.assertEqual(enrollment.irg_practice_center_type_id, practice_type)
        request.write({'state': 'end'})
        self.assertEqual(enrollment.irg_practice_center_type_id, practice_type)

    def test_latest_synced_request_wins(self):
        _course, _student, enrollment = self._make_enrollment('WIN')
        first_type = self._make_practice_type('on_site')
        second_type = self._make_practice_type('on_site_origin')
        first = self._make_request(enrollment, first_type, state='draft')
        first.action_approve()
        second = self._make_request(enrollment, second_type, state='draft')
        second.action_approve()
        self.assertEqual(enrollment.irg_practice_center_type_id, second_type)

    def test_two_courses_are_independent(self):
        _course_a, student, enrollment_a = self._make_enrollment('A')
        today = fields.Date.today()
        course_b = self.env['op.course'].create({
            'name': 'Curso practicas B2',
            'code': 'IRG-PM-B2',
            'lang': self.env.user.lang or 'en_US',
        })
        batch_b = self.env['op.batch'].create({
            'name': 'Lote B2',
            'code': 'IRG-PM-B-B2',
            'course_id': course_b.id,
            'start_date': today,
            'end_date': today + relativedelta(months=1),
        })
        enrollment_b = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': course_b.id,
            'batch_id': batch_b.id,
        })
        type_a = self._make_practice_type('homeclass_sincronas')
        type_b = self._make_practice_type('homeclass_asincronas')
        req_a = self._make_request(enrollment_a, type_a, state='draft')
        req_b = self._make_request(enrollment_b, type_b, state='draft')
        req_a.action_approve()
        req_b.action_approve()
        self.assertEqual(enrollment_a.irg_practice_center_type_id, type_a)
        self.assertEqual(enrollment_b.irg_practice_center_type_id, type_b)

    def test_reject_does_not_clear_enrollment(self):
        _course, _student, enrollment = self._make_enrollment('REJ')
        approved_type = self._make_practice_type('on_site')
        other_type = self._make_practice_type('distance')
        approved = self._make_request(enrollment, approved_type, state='draft')
        approved.action_approve()
        rejected = self._make_request(enrollment, other_type, state='draft')
        rejected.action_reject()
        self.assertEqual(enrollment.irg_practice_center_type_id, approved_type)

    def test_staff_can_write_enrollment_field(self):
        _course, _student, enrollment = self._make_enrollment('STAFF')
        practice_type = self._make_practice_type('tfm_validation')
        enrollment.write({'irg_practice_center_type_id': practice_type.id})
        self.assertEqual(enrollment.irg_practice_center_type_id, practice_type)

    def test_backend_views_include_practice_field(self):
        tree = self.env.ref(
            'irg_student_course_practice_modality.view_op_student_course_tree_practice_modality'
        )
        form = self.env.ref(
            'irg_student_course_practice_modality.view_op_student_course_form_practice_modality'
        )
        for view in (tree, form):
            arch = etree.fromstring(view.arch_db)
            self.assertTrue(
                arch.xpath('//field[@name="irg_practice_center_type_id"]')
            )

    def test_student_helper_returns_course_modality(self):
        course, student, enrollment = self._make_enrollment('HELP')
        practice_type = self._make_practice_type('on_site')
        enrollment.write({'irg_practice_center_type_id': practice_type.id})
        self.assertEqual(
            student.irg_get_practice_center_type(course),
            practice_type,
        )
        other_course = self.env['op.course'].create({
            'name': 'Otro curso HELP',
            'code': 'IRG-PM-HELP2',
            'lang': self.env.user.lang or 'en_US',
        })
        self.assertFalse(student.irg_get_practice_center_type(other_course))

    def test_init_nulls_orphan_student_ids(self):
        _course, _student, enrollment = self._make_enrollment('ORPH')
        self.env.cr.execute("""
            ALTER TABLE op_student_course
            DROP CONSTRAINT IF EXISTS op_student_course_student_id_fkey
        """)
        self.env.cr.execute(
            "UPDATE op_student_course SET student_id = %s WHERE id = %s",
            (2147483647, enrollment.id),
        )
        self.env['op.student.course'].init()
        enrollment.invalidate_recordset(['student_id'])
        self.assertFalse(enrollment.student_id)
