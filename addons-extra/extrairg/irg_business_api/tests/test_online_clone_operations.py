# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import IrgBusinessApiCase


@tagged('post_install', '-at_install', 'irg_business_api')
class TestOnlineCloneOperations(IrgBusinessApiCase):

    def test_preview_online_clone_does_not_write(self):
        before = self.env['slide.channel'].search_count([])
        op = self.run_op('irg_preview_online_clone', {'channel_id': self.channel.id})
        self.assertEqual(op.state, 'verified')
        plan = self.result_json(op)
        self.assertEqual(plan['channel_id'], self.channel.id)
        self.assertGreaterEqual(plan['source_slide_count'], 2)
        self.assertFalse(plan['would_copy_memberships'])
        self.assertEqual(self.env['slide.channel'].search_count([]), before)

    def test_apply_online_clone_copies_content_not_memberships(self):
        source_count = len(self.channel.slide_ids.filtered(
            lambda slide: slide.irg_content_modality in (False, 'homeclass')
            if 'irg_content_modality' in slide._fields else True
        ))
        homeclass_ids = set(self.channel.slide_ids.ids)
        op = self.run_op('irg_apply_online_clone', {
            'channel_id': self.channel.id,
        }, key='clone-1')
        self.assertEqual(op.state, 'preview')
        self.assertFalse(self.channel.irg_online_channel_id)
        self.run_op('irg_approve_operation', {'operation_id': op.id}, key='clone-1-ok')
        self.channel.invalidate_recordset()
        dest = self.channel.irg_online_channel_id
        self.assertTrue(dest)
        self.assertEqual(dest.irg_homeclass_channel_id, self.channel)
        self.assertEqual(len(dest.slide_ids), source_count)
        self.assertFalse(set(dest.slide_ids.ids) & homeclass_ids)
        self.assertFalse(self.env['slide.channel.partner'].search([
            ('channel_id', '=', dest.id),
            ('partner_id', '=', self.partner.id),
        ]))
        op.invalidate_recordset()
        result = self.result_json(op)
        self.assertEqual(result['dest_channel_id'], dest.id)
        self.assertEqual(result['copied_memberships'], 0)

    def test_apply_online_clone_refuses_existing_online_content(self):
        first = self.run_op('irg_apply_online_clone', {
            'channel_id': self.channel.id,
        }, key='clone-first')
        self.run_op('irg_approve_operation', {'operation_id': first.id}, key='clone-first-ok')
        second = self.run_op('irg_apply_online_clone', {
            'channel_id': self.channel.id,
        }, key='clone-second')
        with self.assertRaises(UserError):
            self.run_op('irg_approve_operation', {'operation_id': second.id}, key='clone-second-ok')

    def test_clone_rejects_online_channel_id(self):
        first = self.run_op('irg_apply_online_clone', {
            'channel_id': self.channel.id,
        }, key='clone-src')
        self.run_op('irg_approve_operation', {'operation_id': first.id}, key='clone-src-ok')
        self.channel.invalidate_recordset()
        dest = self.channel.irg_online_channel_id
        with self.assertRaises(UserError):
            self.run_op('irg_preview_online_clone', {'channel_id': dest.id})

    def test_content_reconciliation_reports_missing(self):
        op = self.run_op('irg_preview_content_reconciliation', {
            'channel_id': self.channel.id,
        })
        plan = self.result_json(op)
        self.assertTrue(plan['missing_in_online'])
