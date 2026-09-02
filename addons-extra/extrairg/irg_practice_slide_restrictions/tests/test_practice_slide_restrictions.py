# -*- coding: utf-8 -*-
from contextlib import ExitStack
from dateutil.relativedelta import relativedelta
from lxml import etree
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install', 'irg_practice_slide_restrictions')
class TestPracticeSlideRestrictions(TransactionCase):

    def _make_student_user(self, suffix):
        partner = self.env['res.partner'].create({
            'name': 'Alumno slides %s' % suffix,
            'email': 'slides.%s@example.test' % suffix.lower(),
        })
        user = new_test_user(
            self.env,
            login=partner.email,
            groups='base.group_portal',
            name=partner.name,
        )
        user.partner_id = partner
        student = self.env['op.student'].create({
            'partner_id': partner.id,
            'first_name': 'Alumno',
            'last_name': suffix,
            'gender': 'o',
            'user_id': user.id,
        })
        return student, user

    def _make_course_channel(self, suffix, student):
        today = fields.Date.today()
        course = self.env['op.course'].create({
            'name': 'Curso elearning %s' % suffix,
            'code': 'IRG-PS-%s' % suffix,
            'lang': self.env.user.lang or 'en_US',
        })
        batch = self.env['op.batch'].create({
            'name': 'Lote elearning %s' % suffix,
            'code': 'IRG-PS-B-%s' % suffix,
            'course_id': course.id,
            'start_date': today,
            'end_date': today + relativedelta(months=1),
        })
        channel_vals = {
            'name': 'Canal practicas %s' % suffix,
            'channel_type': 'training',
            'enroll': 'public',
        }
        SlideChannel = self.env['slide.channel']
        if (
            'category_id' in SlideChannel._fields
            and 'moodle.categories' in self.env
        ):
            MoodleCategory = self.env['moodle.categories']
            moodle_category = MoodleCategory.search([], limit=1)
            if not moodle_category:
                moodle_category = MoodleCategory.create({
                    'name': 'IRG Practice Tests',
                })
            channel_vals['category_id'] = moodle_category.id
        with ExitStack() as stack:
            try:
                stack.enter_context(patch(
                    'odoo.addons.odoo_moodle_connector.models.'
                    'slide_channel_custom.utils.get_moodle_credentials',
                    return_value=False,
                ))
            except (ImportError, AttributeError):
                pass
            channel = SlideChannel.create(channel_vals)
        subject = self.env['op.subject'].create({
            'name': 'Practicas %s' % suffix,
            'code': 'IRG-PS-S-%s' % suffix,
            'slide_channel_id': channel.id,
        })
        course.subject_ids = [(4, subject.id)]
        enrollment = self.env['op.student.course'].create({
            'student_id': student.id,
            'course_id': course.id,
            'batch_id': batch.id,
        })
        return course, channel, enrollment

    def _make_section(self, channel, name, required=False):
        vals = {
            'name': name,
            'channel_id': channel.id,
            'is_category': True,
        }
        if required:
            vals['irg_required_practice_type'] = required
        return self.env['slide.slide'].create(vals)

    def test_required_field_exists(self):
        self.assertIn(
            'irg_required_practice_type',
            self.env['slide.slide']._fields,
        )

    def test_empty_requirement_is_visible_to_everyone(self):
        student, user = self._make_student_user('EMPTY')
        _course, channel, _enrollment = self._make_course_channel('EMPTY', student)
        section = self._make_section(channel, 'Comun')
        self.assertTrue(section.is_user_allowed_by_practice_type(user))
        self.assertTrue(
            section.is_user_allowed_by_practice_type(
                self.env.ref('base.public_user')
            )
        )

    def test_required_section_blocks_without_modality(self):
        student, user = self._make_student_user('NONE')
        _course, channel, _enrollment = self._make_course_channel('NONE', student)
        section = self._make_section(channel, 'TFM', required='tfm_validation')
        self.assertFalse(section.is_user_allowed_by_practice_type(user))

    def test_required_section_allows_matching_modality(self):
        student, user = self._make_student_user('MATCH')
        _course, channel, enrollment = self._make_course_channel('MATCH', student)
        practice_type = self.env['practice.center.type'].create({
            'type_of_practice': 'tfm_validation',
        })
        enrollment.irg_practice_center_type_id = practice_type
        section = self._make_section(channel, 'TFM', required='tfm_validation')
        self.assertTrue(section.is_user_allowed_by_practice_type(user))

    def test_required_section_blocks_other_modality(self):
        student, user = self._make_student_user('OTHER')
        _course, channel, enrollment = self._make_course_channel('OTHER', student)
        practice_type = self.env['practice.center.type'].create({
            'type_of_practice': 'on_site',
        })
        enrollment.irg_practice_center_type_id = practice_type
        section = self._make_section(channel, 'TFM', required='tfm_validation')
        self.assertFalse(section.is_user_allowed_by_practice_type(user))

    def test_two_courses_do_not_cross_modalities(self):
        student, user = self._make_student_user('CROSS')
        _course_a, channel_a, enrollment_a = self._make_course_channel('CA', student)
        _course_b, channel_b, enrollment_b = self._make_course_channel('CB', student)
        type_a = self.env['practice.center.type'].create({
            'type_of_practice': 'tfm_validation',
        })
        type_b = self.env['practice.center.type'].create({
            'type_of_practice': 'on_site',
        })
        enrollment_a.irg_practice_center_type_id = type_a
        enrollment_b.irg_practice_center_type_id = type_b
        section_a = self._make_section(channel_a, 'TFM A', required='tfm_validation')
        section_b = self._make_section(channel_b, 'Presencial B', required='on_site')
        self.assertTrue(section_a.is_user_allowed_by_practice_type(user))
        self.assertTrue(section_b.is_user_allowed_by_practice_type(user))
        self.assertFalse(
            self._make_section(
                channel_a, 'Presencial A', required='on_site'
            ).is_user_allowed_by_practice_type(user)
        )
        self.assertFalse(
            self._make_section(
                channel_b, 'TFM B', required='tfm_validation'
            ).is_user_allowed_by_practice_type(user)
        )

    def test_child_inherits_parent_requirement(self):
        student, _user = self._make_student_user('CHILD')
        _course, channel, _enrollment = self._make_course_channel('CHILD', student)
        parent = self._make_section(channel, 'Padre TFM', required='tfm_validation')
        child = self.env['slide.slide'].create({
            'name': 'Hijo TFM',
            'channel_id': channel.id,
            'parent_slide_id': parent.id,
            'inherit_limitations_from_parent': True,
        })
        self.assertEqual(child.irg_required_practice_type, 'tfm_validation')

    def test_error_template_contains_blocked_copy(self):
        view = self.env.ref(
            'irg_practice_slide_restrictions.slide_practice_restriction_error'
        )
        arch = (view.arch_db or '').lower()
        self.assertIn('contenido bloqueado', arch)
        self.assertIn('no puedes visualizar', arch)

    def test_onchange_parent_keeps_batch_and_copies_practice(self):
        student, _user = self._make_student_user('ONCH')
        _course, channel, enrollment = self._make_course_channel('ONCH', student)
        parent = self._make_section(channel, 'Padre ONCH', required='tfm_validation')
        parent.allowed_batch_ids = [(6, 0, [enrollment.batch_id.id])]
        onchange_names = [
            method.__name__
            for method in self.env['slide.slide']._onchange_methods.get(
                'parent_slide_id', []
            )
        ]
        self.assertIn(
            '_onchange_parent_slide_apply_limitations',
            onchange_names,
        )
        child = self.env['slide.slide'].new({
            'name': 'Hijo ONCH',
            'channel_id': channel.id,
            'parent_slide_id': parent.id,
            'inherit_limitations_from_parent': True,
        })
        child._onchange_parent_slide_apply_limitations()
        self.assertEqual(child.irg_required_practice_type, 'tfm_validation')
        self.assertEqual(child.allowed_batch_ids.ids, [enrollment.batch_id.id])

    def test_allows_when_course_linked_only_via_subject_course_id(self):
        student, user = self._make_student_user('SUBJ')
        course, channel, enrollment = self._make_course_channel('SUBJ', student)
        practice_type = self.env['practice.center.type'].create({
            'type_of_practice': 'tfm_validation',
        })
        enrollment.irg_practice_center_type_id = practice_type
        subject = self.env['op.subject'].search(
            [('slide_channel_id', '=', channel.id)],
            limit=1,
        )
        if 'course_id' not in subject._fields:
            self.skipTest('op.subject.course_id is not available')
        subject.write({'course_id': course.id})
        course.write({'subject_ids': [(5, 0, 0)]})
        self.assertFalse(course.subject_ids)
        self.assertEqual(subject.course_id, course)
        section = self._make_section(channel, 'TFM SUBJ', required='tfm_validation')
        self.assertTrue(section.is_user_allowed_by_practice_type(user))

    def test_irg_sections_tab_includes_practice_field(self):
        channel_form = self.env.ref('website_slides.view_slide_channel_form')
        arch = etree.fromstring(channel_form.get_combined_arch())
        self.assertTrue(
            arch.xpath(
                "//field[@name='irg_native_section_ids']/tree/"
                "field[@name='irg_required_practice_type']"
            )
        )
        self.assertTrue(
            arch.xpath(
                "//field[@name='irg_native_section_ids']/form//"
                "field[@name='irg_required_practice_type']"
            )
        )
