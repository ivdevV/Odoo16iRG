# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from lxml import etree

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, new_test_user, tagged

from odoo.addons.irg_practice_request_online_types.models.online_batch import (
    irg_batch_code_is_online_master,
)
from odoo.addons.irg_practice_request_online_types.controllers.main import (
    IrgPracticeRequestOnlineTypes,
)


@tagged('post_install', '-at_install', 'irg_practice_request_online_types')
class TestPracticeRequestOnlineTypes(TransactionCase):

    def test_batch_code_online_detection(self):
        self.assertFalse(irg_batch_code_is_online_master(False))
        self.assertFalse(irg_batch_code_is_online_master(''))
        self.assertFalse(irg_batch_code_is_online_master('MONCHC2505'))
        self.assertFalse(irg_batch_code_is_online_master('MPPCHC2603'))
        self.assertFalse(irg_batch_code_is_online_master('MONLHC2505'))
        self.assertFalse(irg_batch_code_is_online_master('monlhc2505'))
        self.assertFalse(irg_batch_code_is_online_master('MONLPRS2505'))
        self.assertTrue(irg_batch_code_is_online_master('MONLONL2505'))
        self.assertTrue(irg_batch_code_is_online_master('monlonl2505'))
        self.assertTrue(irg_batch_code_is_online_master('MPPCONL2603'))
        self.assertTrue(irg_batch_code_is_online_master('MX123ONL25A'))

    def _make_enrollment(self, suffix, batch_code):
        today = fields.Date.today()
        course_vals = {
            'name': 'Curso online types %s' % suffix,
            'code': 'IRG-OT-%s' % suffix,
        }
        if 'lang' in self.env['op.course']._fields:
            course_vals['lang'] = self.env.user.lang or 'en_US'
        course = self.env['op.course'].create(course_vals)
        batch = self.env['op.batch'].create({
            'name': 'Lote %s' % suffix,
            'code': batch_code,
            'course_id': course.id,
            'start_date': today,
            'end_date': today + relativedelta(months=1),
        })
        partner = self.env['res.partner'].create({
            'name': 'Alumno OT %s' % suffix,
            'email': 'ot.%s@example.test' % suffix.lower(),
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

    def test_enrollment_flag_follows_batch_code(self):
        _student, online = self._make_enrollment('ONL', 'MPPCONL2603')
        _student_hc, homeclass = self._make_enrollment('HC', 'MONLHC2505')
        _student_nl, neurologopedia = self._make_enrollment('NL', 'MONLONL2505')
        self.assertTrue(online.irg_is_online_master_batch)
        self.assertFalse(homeclass.irg_is_online_master_batch)
        self.assertTrue(neurologopedia.irg_is_online_master_batch)

    def test_staff_can_assign_any_type_on_online_enrollment(self):
        _student, enrollment = self._make_enrollment('STAFF', 'MONLONL2505')
        on_site = self.env['practice.center.type'].create({
            'type_of_practice': 'on_site',
        })
        request = self.env['practice.request'].create({
            'name': 'Staff OT',
            'email': 'staff.ot@example.test',
            'course_id': enrollment.id,
            'practice_center_type_id': on_site.id,
        })
        self.assertEqual(request.practice_center_type_id, on_site)

    def test_portal_user_cannot_pick_onsite_for_online_master(self):
        student, enrollment = self._make_enrollment('PORT', 'MPPCONL2603')
        on_site = self.env['practice.center.type'].create({
            'type_of_practice': 'on_site',
        })
        user = new_test_user(
            self.env,
            login='ot.portal@example.test',
            groups='base.group_portal',
            name=student.name,
        )
        user.partner_id = student.partner_id
        student.user_id = user.id
        with self.assertRaises(ValidationError):
            self.env['practice.request'].with_user(user).sudo().create({
                'name': student.name,
                'email': user.login,
                'course_id': enrollment.id,
                'practice_center_type_id': on_site.id,
            })

    def test_portal_user_can_pick_tfm_validation_for_online_master(self):
        student, enrollment = self._make_enrollment('TFM', 'MONLONL2505')
        tfm = self.env['practice.center.type'].create({
            'type_of_practice': 'tfm_validation',
        })
        user = new_test_user(
            self.env,
            login='ot.tfm@example.test',
            groups='base.group_portal',
            name=student.name,
        )
        user.partner_id = student.partner_id
        student.user_id = user.id
        request = self.env['practice.request'].with_user(user).sudo().create({
            'name': student.name,
            'email': user.login,
            'course_id': enrollment.id,
            'practice_center_type_id': tfm.id,
        })
        self.assertEqual(request.practice_center_type_id, tfm)

    def test_portal_user_can_pick_onsite_for_homeclass_neurologopedia(self):
        student, enrollment = self._make_enrollment('NLHC', 'MONLHC2505')
        on_site = self.env['practice.center.type'].create({
            'type_of_practice': 'on_site',
        })
        user = new_test_user(
            self.env,
            login='ot.nlhc@example.test',
            groups='base.group_portal',
            name=student.name,
        )
        user.partner_id = student.partner_id
        student.user_id = user.id
        request = self.env['practice.request'].with_user(user).sudo().create({
            'name': student.name,
            'email': user.login,
            'course_id': enrollment.id,
            'practice_center_type_id': on_site.id,
        })
        self.assertEqual(request.practice_center_type_id, on_site)

    def test_controller_error_helper_blocks_onsite_on_online_batch(self):
        _student, enrollment = self._make_enrollment('CTL', 'MPPCONL2603')
        on_site = self.env['practice.center.type'].create({
            'type_of_practice': 'on_site',
        })
        async_type = self.env['practice.center.type'].create({
            'type_of_practice': 'homeclass_asincronas',
        })
        controller = IrgPracticeRequestOnlineTypes()
        self.assertTrue(controller._irg_online_practice_type_error({
            'course_id': str(enrollment.id),
            'practice_center_type_id': str(on_site.id),
        }, env=self.env))
        self.assertFalse(controller._irg_online_practice_type_error({
            'course_id': str(enrollment.id),
            'practice_center_type_id': str(async_type.id),
        }, env=self.env))

    def test_portal_template_marks_online_options(self):
        view = self.env.ref(
            'irg_practice_request_online_types.practice_request_form_online_types'
        )
        arch = etree.fromstring(view.arch_db)
        self.assertTrue(arch.xpath("//attribute[@name='t-att-data-irg-online']"))
        self.assertTrue(arch.xpath("//attribute[@name='t-att-data-irg-online-ok']"))
        script = '\n'.join(arch.xpath('//script/text()'))
        self.assertIn('irgApplyOnlinePracticeFilter', script)
        self.assertIn('setTimeout', script)
        self.assertIn('dispatchEvent', script)
        self.assertNotIn('option.hidden = isOnline', script)
