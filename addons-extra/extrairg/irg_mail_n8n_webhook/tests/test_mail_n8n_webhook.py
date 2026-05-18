# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestMailN8nWebhook(TransactionCase):
    def setUp(self):
        super().setUp()
        self.params = self.env['ir.config_parameter'].sudo()
        self.params.set_param('irg_mail_n8n_webhook.enabled', 'True')
        self.params.set_param('irg_mail_n8n_webhook.webhook_url', 'https://n8n.example.test/webhook/mail')
        self.params.set_param('irg_mail_n8n_webhook.auth_token', 'test-token')
        self.params.set_param('irg_mail_n8n_webhook.max_attempts', '2')
        self.params.set_param('irg_mail_n8n_webhook.max_attachment_mb', '1')
        self.service = self.env['irg.mail.n8n.service']
        self.mail = self.env['mail.mail'].create({
            'subject': 'Correo de prueba n8n',
            'body_html': '<p>Contenido</p>',
            'email_from': 'odoo@example.test',
            'email_to': 'student@example.test',
        })

    def test_build_payload_includes_core_mail_data(self):
        delivery = self.service._get_or_create_delivery(self.mail)

        payload = self.service._build_payload(self.mail, delivery)

        self.assertEqual(payload['mail']['id'], self.mail.id)
        self.assertEqual(payload['mail']['subject'], 'Correo de prueba n8n')
        self.assertEqual(payload['mail']['email_to'], 'student@example.test')
        self.assertEqual(payload['idempotency_key'], delivery.idempotency_key)

    def test_send_marks_mail_as_sent_on_success(self):
        with patch.object(type(self.service), '_post_json', return_value=(202, '{"ok": true}')):
            result = self.mail.send()

        delivery = self.env['irg.mail.n8n.delivery'].search([('mail_id', '=', self.mail.id)])

        self.assertTrue(result)
        self.assertEqual(self.mail.state, 'sent')
        self.assertEqual(delivery.state, 'sent')
        self.assertEqual(delivery.attempt_count, 1)

    def test_direct_send_interception_marks_mail_as_sent_on_success(self):
        with patch.object(type(self.service), '_post_json', return_value=(202, '{"ok": true}')):
            result = self.mail._send()

        delivery = self.env['irg.mail.n8n.delivery'].search([('mail_id', '=', self.mail.id)])

        self.assertTrue(result)
        self.assertEqual(self.mail.state, 'sent')
        self.assertEqual(delivery.state, 'sent')

    def test_send_schedules_retry_on_http_failure(self):
        with patch.object(type(self.service), '_post_json', return_value=(500, 'server error')):
            result = self.mail.send()

        delivery = self.env['irg.mail.n8n.delivery'].search([('mail_id', '=', self.mail.id)])

        self.assertFalse(result)
        self.assertEqual(self.mail.state, 'outgoing')
        self.assertEqual(delivery.state, 'failed')
        self.assertEqual(delivery.attempt_count, 1)
        self.assertTrue(delivery.next_attempt_at)

    def test_mail_moves_to_exception_when_retries_are_exhausted(self):
        with patch.object(type(self.service), '_post_json', return_value=(500, 'server error')):
            self.mail.send()
            delivery = self.env['irg.mail.n8n.delivery'].search([('mail_id', '=', self.mail.id)])
            delivery.write({'next_attempt_at': False})
            self.env['irg.mail.n8n.delivery']._cron_retry_pending_deliveries()

        delivery = self.env['irg.mail.n8n.delivery'].search([('mail_id', '=', self.mail.id)])

        self.assertEqual(delivery.attempt_count, 2)
        self.assertEqual(self.mail.state, 'exception')
        self.assertEqual(delivery.state, 'failed')
        self.assertFalse(delivery.next_attempt_at)

    def test_disabled_module_delegates_to_native_send(self):
        self.params.set_param('irg_mail_n8n_webhook.enabled', 'False')

        with patch('odoo.addons.mail.models.mail_mail.MailMail.send', return_value=True) as native_send:
            result = self.mail.send()

        self.assertTrue(result)
        native_send.assert_called_once()