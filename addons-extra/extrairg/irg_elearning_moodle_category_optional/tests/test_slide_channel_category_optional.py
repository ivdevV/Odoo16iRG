# -*- coding: utf-8 -*-

from unittest.mock import patch

from lxml import etree

from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'irg_elearning_moodle_category_optional')
class TestSlideChannelCategoryOptional(TransactionCase):

    def test_category_field_contract_is_optional(self):
        category_field = self.env['slide.channel']._fields['category_id']

        self.assertFalse(category_field.required)
        self.assertEqual(category_field.comodel_name, 'moodle.categories')
        self.assertEqual(category_field.string, 'Course Category')

    def test_course_without_moodle_category_can_be_created_and_updated(self):
        credentials_patch = patch(
            'odoo.addons.odoo_moodle_connector.models.slide_channel_custom.'
            'utils.get_moodle_credentials',
            return_value=False,
        )
        with credentials_patch:
            channel = self.env['slide.channel'].create({
                'name': 'Course without Moodle category',
                'channel_type': 'training',
                'enroll': 'public',
                'category_id': False,
            })
            channel.write({'name': 'Updated course without Moodle category'})

        self.assertFalse(channel.category_id)
        self.assertEqual(channel.name, 'Updated course without Moodle category')

    def test_effective_form_view_marks_category_as_optional(self):
        view = self.env.ref(
            'irg_elearning_moodle_category_optional.'
            'slide_channel_form_optional_moodle_category'
        )

        architecture = self.env['slide.channel'].get_view(
            view_id=view.id,
            view_type='form',
        )['arch']
        nodes = etree.fromstring(architecture.encode()).xpath(
            "//page[@name='moodle']//field[@name='category_id']"
        )

        self.assertTrue(nodes)
        self.assertTrue(all(node.get('required') == '0' for node in nodes))
