# -*- coding: utf-8 -*-

from unittest.mock import patch

from dateutil.relativedelta import relativedelta
from lxml import etree

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged

from odoo.addons.irg_practice_request_eligibility.controllers.main import (
    IrgPracticeRequestEligibility,
)


@tagged('post_install', '-at_install', 'irg_practice_request_eligibility')
class TestPracticeRequestEligibility(TransactionCase):

    def _make_enrollment(self, suffix, course_code):
        today = fields.Date.today()
        course_vals = {
            'name': 'Curso elegibilidad %s' % suffix,
            'code': course_code,
        }
        if 'lang' in self.env['op.course']._fields:
            course_vals['lang'] = self.env.user.lang or 'en_US'
        course = self.env['op.course'].create(course_vals)
        batch = self.env['op.batch'].create({
            'name': 'Lote %s' % suffix,
            'code': 'ELG%s' % suffix,
            'course_id': course.id,
            'start_date': today,
            'end_date': today + relativedelta(months=1),
        })
        partner = self.env['res.partner'].create({
            'name': 'Alumno ELG %s' % suffix,
            'email': 'elg.%s@example.test' % suffix.lower(),
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
        return student, enrollment

    def _with_completion(self, enrollment, percentage):
        return patch.object(
            type(enrollment),
            '_irg_practice_completion_percentage',
            return_value=percentage,
        )

    def test_fifty_percent_non_diplomado_can_request(self):
        _student, enrollment = self._make_enrollment('OK50', 'MST-ELG-50')
        with self._with_completion(enrollment, 50.0):
            self.assertFalse(enrollment.irg_practice_request_block_reason())
            self.assertTrue(enrollment.irg_can_request_practice())

    def test_below_fifty_percent_cannot_request(self):
        _student, enrollment = self._make_enrollment('LOW', 'MST-ELG-LOW')
        with self._with_completion(enrollment, 49.99):
            self.assertEqual(
                enrollment.irg_practice_request_block_reason(), 'completion'
            )
            self.assertFalse(enrollment.irg_can_request_practice())

    def test_diplomado_cannot_request_even_at_full_progress(self):
        _student, enrollment = self._make_enrollment('DIP', 'DI-ELG-FULL')
        self.assertTrue(enrollment.course_id.irg_excludes_practice_request())
        with self._with_completion(enrollment, 100.0):
            self.assertEqual(
                enrollment.irg_practice_request_block_reason(), 'diplomado'
            )
            self.assertFalse(enrollment.irg_can_request_practice())

    def test_diplomado_progress_does_not_unlock_another_course(self):
        student, diplomado = self._make_enrollment('MIXD', 'DI-ELG-MIX')
        _other_student, master_source = self._make_enrollment('MIXM', 'MST-ELG-MIX')
        master = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': master_source.course_id.id,
            'batch_id': master_source.batch_id.id,
        })

        def percentage(enrollment, low_master):
            if enrollment.course_id.irg_excludes_practice_request():
                return 100.0
            return 40.0 if low_master else 50.0

        with patch.object(
            type(diplomado),
            '_irg_practice_completion_percentage',
            autospec=True,
            side_effect=lambda enrollment: percentage(enrollment, True),
        ):
            self.assertFalse(diplomado.irg_can_request_practice())
            self.assertFalse(master.irg_can_request_practice())
            self.assertFalse(student.irg_can_request_any_practice())

        with patch.object(
            type(diplomado),
            '_irg_practice_completion_percentage',
            autospec=True,
            side_effect=lambda enrollment: percentage(enrollment, False),
        ):
            self.assertFalse(diplomado.irg_can_request_practice())
            self.assertTrue(master.irg_can_request_practice())
            self.assertTrue(student.irg_can_request_any_practice())

    def _portal_user(self, student, login):
        user = new_test_user(
            self.env,
            login=login,
            groups='base.group_portal',
            name=student.name,
        )
        user.partner_id = student.partner_id
        student.user_id = user.id
        return user

    def _practice_type(self):
        return self.env['practice.center.type'].create({
            'type_of_practice': 'on_site',
        })

    def test_portal_user_cannot_create_below_fifty(self):
        student, enrollment = self._make_enrollment('PORTLOW', 'MST-ELG-PORTLOW')
        user = self._portal_user(student, 'elg.portal.low@example.test')
        with self._with_completion(enrollment, 49.99):
            with self.assertRaises(ValidationError):
                self.env['practice.request'].with_user(user).sudo().create({
                    'name': student.name,
                    'email': user.login,
                    'course_id': enrollment.id,
                    'practice_center_type_id': self._practice_type().id,
                })

    def test_portal_user_cannot_create_diplomado(self):
        student, enrollment = self._make_enrollment('PORTDIP', 'DI-ELG-PORT')
        user = self._portal_user(student, 'elg.portal.dip@example.test')
        with self._with_completion(enrollment, 100.0):
            with self.assertRaises(ValidationError) as caught:
                self.env['practice.request'].with_user(user).sudo().create({
                    'name': student.name,
                    'email': user.login,
                    'course_id': enrollment.id,
                    'practice_center_type_id': self._practice_type().id,
                })
        self.assertIn('diplomado', str(caught.exception).lower())

    def test_portal_user_can_create_at_fifty(self):
        student, enrollment = self._make_enrollment('PORTOK', 'MST-ELG-PORTOK')
        user = self._portal_user(student, 'elg.portal.ok@example.test')
        practice_type = self._practice_type()
        with self._with_completion(enrollment, 50.0):
            request = self.env['practice.request'].with_user(user).sudo().create({
                'name': student.name,
                'email': user.login,
                'course_id': enrollment.id,
                'practice_center_type_id': practice_type.id,
            })
        self.assertEqual(request.course_id, enrollment)

    def test_staff_can_create_without_eligibility(self):
        _student, enrollment = self._make_enrollment('STAFF', 'DI-ELG-STAFF')
        with self._with_completion(enrollment, 0.0):
            request = self.env['practice.request'].create({
                'name': 'Staff ELG',
                'email': 'staff.elg@example.test',
                'course_id': enrollment.id,
                'practice_center_type_id': self._practice_type().id,
            })
        self.assertEqual(request.course_id, enrollment)

    def test_controller_error_blocks_low_progress_and_diplomado(self):
        _student, low = self._make_enrollment('CTLLOW', 'MST-ELG-CTLLOW')
        _student_dip, diplomado = self._make_enrollment('CTLDIP', 'DI-ELG-CTL')
        controller = IrgPracticeRequestEligibility()
        with self._with_completion(low, 10.0):
            self.assertIn(
                '50%',
                controller._irg_practice_eligibility_error(
                    {'course_id': str(low.id)}, env=self.env
                ),
            )
        with self._with_completion(diplomado, 90.0):
            self.assertIn(
                'diplomado',
                controller._irg_practice_eligibility_error(
                    {'course_id': str(diplomado.id)}, env=self.env
                ).lower(),
            )
        with self._with_completion(low, 80.0):
            self.assertFalse(controller._irg_practice_eligibility_error(
                {'course_id': str(low.id)}, env=self.env
            ))

    def test_templates_gate_practice_entry_points(self):
        tile = self.env.ref(
            'irg_practice_request_eligibility.course_tile_practice_eligibility'
        )
        form = self.env.ref(
            'irg_practice_request_eligibility.practice_request_form_eligibility'
        )
        listing = self.env.ref(
            'irg_practice_request_eligibility.practice_request_list_eligibility'
        )
        menu = self.env.ref(
            'irg_practice_request_eligibility.portal_menu_practice_eligibility'
        )
        tile_arch = etree.fromstring(tile.arch_db)
        form_arch = etree.fromstring(form.arch_db)
        list_arch = etree.fromstring(listing.arch_db)
        menu_arch = etree.fromstring(menu.arch_db)
        self.assertIn(
            'irg_portal_practice_allowed_for_course',
            tile_arch.xpath('//attribute[@name="t-if"]')[0].text,
        )
        form_conditions = form_arch.xpath('//attribute[@name="t-if"]/text()')
        self.assertTrue(any('irg_can_request_practice' in text for text in form_conditions))
        self.assertIn(
            'irg_can_request_practice',
            list_arch.xpath('//attribute[@name="t-if"]')[0].text,
        )
        menu_condition = menu_arch.xpath('//attribute[@name="t-if"]')[0].text
        self.assertIn('irg_is_practice_menu', menu_condition)
        self.assertIn("('partner_id', '=', user.partner_id.id)", menu_condition)

    def test_empty_student_recordset_cannot_request_practice(self):
        self.assertFalse(
            self.env['op.student'].browse().irg_can_request_any_practice()
        )

    def test_portal_user_cannot_submit_another_students_enrollment(self):
        _owner, eligible = self._make_enrollment('OWNER', 'MST-ELG-OWNER')
        intruder_student, _own = self._make_enrollment('INTR', 'MST-ELG-INTR')
        intruder = self._portal_user(intruder_student, 'elg.intruder@example.test')
        controller = IrgPracticeRequestEligibility()
        with self._with_completion(eligible, 80.0):
            with self.assertRaises(ValidationError) as caught:
                self.env['practice.request'].with_user(intruder).sudo().create({
                    'name': intruder_student.name,
                    'email': intruder.login,
                    'course_id': eligible.id,
                    'practice_center_type_id': self._practice_type().id,
                })
            self.assertIn('no es tuya', str(caught.exception).lower())
            self.assertIn(
                'no es tuya',
                controller._irg_practice_eligibility_error(
                    {'course_id': str(eligible.id)},
                    env=self.env(user=intruder),
                ).lower(),
            )
