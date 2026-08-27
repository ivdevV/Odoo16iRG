# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import IrgBusinessApiCase


@tagged('post_install', '-at_install', 'irg_business_api')
class TestIdempotencyAndConcurrency(IrgBusinessApiCase):

    def test_same_key_same_hash_does_not_duplicate(self):
        payload = {
            'channel_id': self.channel.id,
            'name': 'Idempotent article',
            'html_content': '<p>Once</p>',
        }
        first = self.run_op('irg_create_slide_draft', payload, key='idem-1')
        self.run_op('irg_approve_operation', {'operation_id': first.id}, key='idem-1-ok')
        first.invalidate_recordset()
        slide_id = self.result_json(first)['id']
        second = self.run_op('irg_create_slide_draft', payload, key='idem-1')
        self.assertEqual(second.id, first.id)
        copies = self.env['slide.slide'].search([
            ('channel_id', '=', self.channel.id),
            ('name', '=', 'Idempotent article'),
        ])
        self.assertEqual(len(copies), 1)
        self.assertEqual(copies.id, slide_id)

    def test_same_key_different_payload_rejected(self):
        self.run_op('irg_create_slide_draft', {
            'channel_id': self.channel.id,
            'name': 'A',
            'html_content': '<p>A</p>',
        }, key='clash-1')
        with self.assertRaises(UserError):
            self.run_op('irg_create_slide_draft', {
                'channel_id': self.channel.id,
                'name': 'B',
                'html_content': '<p>B</p>',
            }, key='clash-1')

    def test_concurrent_change_between_preview_and_apply(self):
        op = self.run_op('irg_update_slide_draft', {
            'slide_id': self.draft_slide.id,
            'name': 'From preview',
        }, key='race-1')
        self.draft_slide.write({'name': 'Changed underneath'})
        with self.assertRaises(UserError):
            self.run_op('irg_approve_operation', {'operation_id': op.id}, key='race-1-ok')
        self.draft_slide.invalidate_recordset()
        self.assertEqual(self.draft_slide.name, 'Changed underneath')

    def test_oversized_payload_rejected_before_apply(self):
        huge = '{"note": "%s"}' % ('a' * 70000)
        with self.assertRaises(UserError):
            self.api_env().create({
                'operation_code': 'irg_list_courses',
                'environment': 'test',
                'request_payload': huge,
                'idempotency_key': 'huge-1',
            })
