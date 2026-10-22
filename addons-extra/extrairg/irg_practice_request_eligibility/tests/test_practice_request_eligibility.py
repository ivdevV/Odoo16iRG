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

    def test_sixty_percent_non_diplomado_can_request(self):
        _student, enrollment = self._make_enrollment('OK60', 'MST-ELG-60')
        with self._with_completion(enrollment, 60.0):
            self.assertFalse(enrollment.irg_practice_request_block_reason())
            self.assertTrue(enrollment.irg_can_request_practice())

    def test_nc_part_one_opens_at_twenty_five_and_part_two_stays_at_sixty(self):
        _student, enrollment = self._make_enrollment('NC25', 'NC')
        _student_mnc, mnc = self._make_enrollment('MNC25', 'MNC')
        controller = IrgPracticeRequestEligibility()
        with self._with_completion(enrollment, 24.99):
            self.assertEqual(
                enrollment.irg_practice_request_block_reason(), 'completion'
            )
            self.assertFalse(enrollment.irg_can_request_practice())
        with self._with_completion(enrollment, 25.0):
            self.assertTrue(enrollment.irg_can_request_practice())
            self.assertTrue(enrollment.irg_can_request_practice_part('1'))
            self.assertFalse(enrollment.irg_can_request_practice_part('2'))
            self.assertIn('25%', enrollment.irg_practice_locked_message())
            self.assertIn(
                'parte 2',
                enrollment.irg_practice_part_error('2').lower(),
            )
            self.assertIn(
                'parte 1',
                controller._irg_practice_eligibility_error(
                    {'course_id': str(enrollment.id)}, env=self.env
                ).lower(),
            )
        with self._with_completion(mnc, 60.0):
            self.assertTrue(mnc.irg_can_request_practice_part('1'))
            self.assertTrue(mnc.irg_can_request_practice_part('2'))
            self.assertFalse(mnc.irg_practice_part_error('2'))

    def test_below_sixty_percent_cannot_request(self):
        _student, enrollment = self._make_enrollment('LOW', 'MST-ELG-LOW')
        with self._with_completion(enrollment, 59.99):
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
            return 40.0 if low_master else 60.0

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

    def _location(self):
        country = self.env['res.country'].search([('code', '=', 'ES')], limit=1)
        if not country:
            country = self.env['res.country'].create({
                'name': 'Pais ELG',
                'code': 'Z9',
            })
        state = self.env['res.country.state'].search([
            ('country_id', '=', country.id),
        ], limit=1)
        if not state:
            state = self.env['res.country.state'].create({
                'name': 'Ciudad ELG',
                'code': 'ELG',
                'country_id': country.id,
            })
        return country, state

    def test_portal_user_can_create_at_sixty_with_location(self):
        student, enrollment = self._make_enrollment('PORTOK', 'MST-ELG-PORTOK')
        user = self._portal_user(student, 'elg.portal.ok@example.test')
        practice_type = self._practice_type()
        country, state = self._location()
        with self._with_completion(enrollment, 60.0):
            request = self.env['practice.request'].with_user(user).sudo().create({
                'name': student.name,
                'email': user.login,
                'course_id': enrollment.id,
                'practice_center_type_id': practice_type.id,
                'country_id': country.id,
                'state_id': state.id,
            })
        self.assertEqual(request.course_id, enrollment)

    def test_portal_user_cannot_create_without_country_or_city(self):
        student, enrollment = self._make_enrollment('PORTLOC', 'MST-ELG-PORTLOC')
        user = self._portal_user(student, 'elg.portal.loc@example.test')
        country, _state = self._location()
        controller = IrgPracticeRequestEligibility()
        with self._with_completion(enrollment, 80.0):
            with self.assertRaises(ValidationError) as caught:
                self.env['practice.request'].with_user(user).sudo().create({
                    'name': student.name,
                    'email': user.login,
                    'course_id': enrollment.id,
                    'practice_center_type_id': self._practice_type().id,
                    'country_id': country.id,
                })
        self.assertIn('ciudad', str(caught.exception).lower())
        self.assertIn(
            'país',
            controller._irg_practice_location_error({}, env=self.env).lower(),
        )

    def test_nc_portal_part_one_at_twenty_five_and_part_two_at_sixty(self):
        student, enrollment = self._make_enrollment('NCPORT', 'NC')
        user = self._portal_user(student, 'elg.portal.nc@example.test')
        country, state = self._location()
        practice_type = self._practice_type()

        def _create(part):
            return self.env['practice.request'].with_user(user).sudo().create({
                'name': student.name,
                'email': user.login,
                'course_id': enrollment.id,
                'practice_center_type_id': practice_type.id,
                'country_id': country.id,
                'state_id': state.id,
                'irg_practice_part': part,
            })

        with self._with_completion(enrollment, 25.0):
            with self.assertRaises(ValidationError) as caught:
                _create('2')
            self.assertIn('parte 2', str(caught.exception).lower())
            part_one = _create('1')
        self.assertEqual(part_one.irg_practice_part, '1')
        self.assertFalse(part_one.irg_blocking_same_part('2'))
        self.assertEqual(part_one.irg_blocking_same_part('1'), part_one)
        with self._with_completion(enrollment, 60.0):
            part_two = _create('2')
        self.assertEqual(part_two.irg_practice_part, '2')

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
                '60%',
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
        tile_conditions = '\n'.join(tile_arch.xpath('//attribute[@name="t-if"]/text()'))
        tile_text = '\n'.join(tile_arch.xpath('//p/text()'))
        self.assertIn('irg_portal_practice_allowed_for_course', tile_conditions)
        self.assertIn('irg_excludes_practice_request', tile_conditions)
        self.assertIn(
            'el 60% de los módulos correspondientes al programa formativo',
            tile_text,
        )
        self.assertIn('el 25% de los módulos', tile_text)
        self.assertFalse(tile_arch.xpath('.//a'))
        form_conditions = form_arch.xpath('//attribute[@name="t-if"]/text()')
        self.assertTrue(any('irg_can_request_practice' in text for text in form_conditions))
        form_labels = form_arch.xpath('//label/text()')
        self.assertIn('País en donde realizaras las prácticas', form_labels)
        self.assertIn('Ciudad en donde realizaras las prácticas', form_labels)
        self.assertIn('Parte de las prácticas', form_labels)
        self.assertEqual(
            form_arch.xpath('//attribute[@name="required"]/text()').count('required'),
            2,
        )
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
