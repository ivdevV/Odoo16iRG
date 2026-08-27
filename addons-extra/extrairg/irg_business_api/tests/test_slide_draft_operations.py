# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import IrgBusinessApiCase


@tagged('post_install', '-at_install', 'irg_business_api')
class TestSlideDraftOperations(IrgBusinessApiCase):

    def test_create_slide_draft_is_preview_only(self):
        before = self.env['slide.slide'].search_count([('channel_id', '=', self.channel.id)])
        op = self.run_op('irg_create_slide_draft', {
            'channel_id': self.channel.id,
            'name': 'New article',
            'html_content': '<p>Hello</p>',
            'sequence': 30,
            'irg_section_id': self.section.id,
            'is_published': True,
        })
        self.assertEqual(op.state, 'preview')
        after = self.env['slide.slide'].search_count([('channel_id', '=', self.channel.id)])
        self.assertEqual(after, before)
        proposed = self.proposed_json(op)
        self.assertEqual(proposed['is_published'], False)
        self.assertEqual(proposed['slide_category'], 'article')

    def test_approve_create_slide_draft_creates_unpublished_article(self):
        before_ids = set(self.env['slide.slide'].search([
            ('channel_id', '=', self.channel.id),
        ]).ids)
        op = self.run_op('irg_create_slide_draft', {
            'channel_id': self.channel.id,
            'name': 'Approved article',
            'html_content': '<p>Body</p>',
            'irg_section_id': self.section.id,
        }, key='create-slide-1')
        approve = self.run_op('irg_approve_operation', {
            'operation_id': op.id,
        }, key='approve-create-slide-1')
        self.assertEqual(approve.state, 'verified')
        op.invalidate_recordset()
        self.assertEqual(op.state, 'verified')
        created = self.env['slide.slide'].search([
            ('channel_id', '=', self.channel.id),
            ('id', 'not in', list(before_ids)),
        ])
        self.assertEqual(len(created), 1)
        self.assertEqual(created.slide_category, 'article')
        self.assertFalse(created.is_published)
        self.assertEqual(created.name, 'Approved article')
        self.assertEqual(created.channel_id, self.channel)
        result = self.result_json(op)
        self.assertEqual(result['id'], created.id)

    def test_update_draft_rejects_published_slide(self):
        op = self.run_op('irg_update_slide_draft', {
            'slide_id': self.published_slide.id,
            'name': 'Hacked',
        })
        self.assertEqual(op.state, 'preview')
        with self.assertRaises(UserError):
            self.run_op('irg_approve_operation', {'operation_id': op.id})
        self.published_slide.invalidate_recordset()
        self.assertEqual(self.published_slide.name, 'Published lesson')

    def test_update_draft_allowlisted_fields(self):
        op = self.run_op('irg_update_slide_draft', {
            'slide_id': self.draft_slide.id,
            'name': 'Renamed draft',
            'html_content': '<p>Updated</p>',
        }, key='upd-draft-1')
        self.run_op('irg_approve_operation', {'operation_id': op.id}, key='approve-upd-draft-1')
        self.draft_slide.invalidate_recordset()
        self.assertEqual(self.draft_slide.name, 'Renamed draft')

    def test_update_rejects_unknown_fields(self):
        with self.assertRaises(UserError):
            self.run_op('irg_update_slide_draft', {
                'slide_id': self.draft_slide.id,
                'user_id': self.plain_user.id,
            })

    def test_create_and_reorder_section(self):
        op = self.run_op('irg_create_course_section', {
            'channel_id': self.channel.id,
            'name': 'New section',
            'sequence': 50,
        }, key='sec-1')
        self.run_op('irg_approve_operation', {'operation_id': op.id}, key='approve-sec-1')
        op.invalidate_recordset()
        section_id = self.result_json(op)['id']
        section = self.env['irg.slide.section'].browse(section_id)
        self.assertEqual(section.channel_id, self.channel)
        reorder = self.run_op('irg_reorder_course_section', {
            'channel_id': self.channel.id,
            'section_ids': [section.id, self.section.id],
        }, key='reorder-1')
        self.run_op('irg_approve_operation', {'operation_id': reorder.id}, key='approve-reorder-1')
        section.invalidate_recordset()
        self.section.invalidate_recordset()
        self.assertLess(section.sequence, self.section.sequence)

    def test_publish_is_separate_confirmation(self):
        create = self.run_op('irg_create_slide_draft', {
            'channel_id': self.channel.id,
            'name': 'To publish',
            'html_content': '<p>X</p>',
        }, key='pub-create')
        self.run_op('irg_approve_operation', {'operation_id': create.id}, key='pub-create-ok')
        create.invalidate_recordset()
        slide_id = self.result_json(create)['id']
        slide = self.env['slide.slide'].browse(slide_id)
        self.assertFalse(slide.is_published)
        publish = self.run_op('irg_publish_slide', {'slide_id': slide_id}, key='pub-1')
        self.run_op('irg_approve_operation', {'operation_id': publish.id}, key='pub-1-ok')
        slide.invalidate_recordset()
        self.assertTrue(slide.is_published)
        unpublish = self.run_op('irg_unpublish_slide', {'slide_id': slide_id}, key='unpub-1')
        self.run_op('irg_approve_operation', {'operation_id': unpublish.id}, key='unpub-1-ok')
        slide.invalidate_recordset()
        self.assertFalse(slide.is_published)

    def test_html_over_limit_rejected(self):
        with self.assertRaises(UserError):
            self.run_op('irg_create_slide_draft', {
                'channel_id': self.channel.id,
                'name': 'Huge',
                'html_content': 'x' * 40000,
            })
