# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import tagged

from .common import IrgBusinessApiCase


@tagged('post_install', '-at_install', 'irg_business_api')
class TestAccessPermissions(IrgBusinessApiCase):

    def test_plain_user_cannot_create_operation(self):
        with self.assertRaises(AccessError):
            self.run_op('irg_list_courses', {'limit': 5}, user=self.plain_user)

    def test_plain_user_cannot_call_private_dispatch(self):
        op = self.run_op('irg_list_courses', {'limit': 5})
        with self.assertRaises(AccessError):
            self.env['irg.api.operation'].with_user(self.plain_user).browse(op.id)._irg_dispatch()

    def test_write_cannot_forge_applied_state(self):
        op = self.run_op('irg_create_slide_draft', {
            'channel_id': self.channel.id,
            'name': 'Forge me',
            'html_content': '<p>x</p>',
        })
        with self.assertRaises(AccessError):
            op.with_user(self.api_user).write({'state': 'applied'})
        with self.assertRaises(AccessError):
            op.with_user(self.api_user).with_context(irg_api_internal=True).write({
                'state': 'applied',
                'proposed_after': '{"is_published": true}',
            })
        op.invalidate_recordset()
        self.assertEqual(op.state, 'preview')
        self.assertFalse(self.env['slide.slide'].search([
            ('name', '=', 'Forge me'),
            ('channel_id', '=', self.channel.id),
        ]))

    def test_unlink_denied(self):
        op = self.run_op('irg_list_courses', {'limit': 5})
        with self.assertRaises(AccessError):
            op.with_user(self.api_user).unlink()
        with self.assertRaises(AccessError):
            op.sudo().unlink()

    def test_client_cannot_set_requested_by(self):
        op = self.api_env().create({
            'operation_code': 'irg_list_courses',
            'environment': 'test',
            'request_payload': '{"limit": 5}',
            'idempotency_key': 'owner-1',
            'requested_by': self.plain_user.id,
            'state': 'applied',
        })
        self.assertEqual(op.requested_by, self.api_user)
        self.assertEqual(op.state, 'verified')

    def test_unknown_operation_rejected(self):
        with self.assertRaises(UserError):
            self.run_op('execute_kw', {'model': 'slide.slide'})

    def test_clone_wrong_payload_keys_rejected(self):
        with self.assertRaises(UserError):
            self.run_op('irg_apply_online_clone', {'source_id': 1, 'dest_id': 2})
