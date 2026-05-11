# -*- coding: utf-8 -*-

import base64

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestScholarshipWebhook(TransactionCase):
    def setUp(self):
        super().setUp()
        self.service = self.env['irg.scholarship.webhook.service'].sudo()
        self.env['ir.config_parameter'].sudo().set_param(
            'irg_student_scholarship_webhook.token',
            'test-token',
        )
        self.partner = self.env['res.partner'].create({
            'name': 'Alumno Webhook',
            'email': 'alumno.webhook@example.com',
        })
        self.scholarship_type = self.env['op.scholarship.type'].create({
            'name': 'Beca Merito Academico',
            'amount': 999,
        })

    def _payload(self, **overrides):
        payload = {
            'email': self.partner.email,
            'document_name': 'Solicitud de beca',
            'filename': 'solicitud.pdf',
            'document_content_base64': base64.b64encode(b'pdf-content').decode('ascii'),
            'note': 'Recibido desde integracion externa',
        }
        payload.update(overrides)
        return payload

    def test_validate_authorization_requires_bearer_token(self):
        result = self.service.validate_authorization(None)

        self.assertEqual(result['error'], 'missing_token')

    def test_validate_authorization_rejects_invalid_token(self):
        result = self.service.validate_authorization('Bearer wrong-token')

        self.assertEqual(result['error'], 'invalid_token')

    def test_process_payload_rejects_unknown_email(self):
        result, status = self.service.process_payload(self._payload(email='missing@example.com'))

        self.assertEqual(status, 404)
        self.assertEqual(result['error'], 'partner_not_found')

    def test_process_payload_rejects_missing_required_field(self):
        result, status = self.service.process_payload(self._payload(filename=''))

        self.assertEqual(status, 400)
        self.assertEqual(result['error'], 'missing_required_field')

        result, status = self.service.process_payload(
            self._payload(document_content_base64=False)
        )

        self.assertEqual(status, 400)
        self.assertEqual(result['error'], 'missing_required_field')

    def test_process_payload_rejects_ambiguous_partner_email(self):
        self.env['res.partner'].create({
            'name': 'Alumno Webhook Duplicado',
            'email': self.partner.email,
        })
        result, status = self.service.process_payload(self._payload())

        self.assertEqual(status, 409)
        self.assertEqual(result['error'], 'ambiguous_email')

    def test_process_payload_rejects_invalid_base64(self):
        result, status = self.service.process_payload(
            self._payload(document_content_base64='not-valid-base64')
        )

        self.assertEqual(status, 400)
        self.assertEqual(result['error'], 'invalid_base64')

    def test_process_payload_rejects_invalid_extension(self):
        result, status = self.service.process_payload(self._payload(filename='solicitud.exe'))

        self.assertEqual(status, 400)
        self.assertEqual(result['error'], 'invalid_file_extension')

    def test_process_payload_rejects_empty_file(self):
        result, status = self.service.process_payload(
            self._payload(document_content_base64=base64.b64encode(b'').decode('ascii'))
        )

        self.assertEqual(status, 400)
        self.assertEqual(result['error'], 'empty_file')

    def test_process_payload_creates_scholarship_document(self):
        result, status = self.service.process_payload(self._payload())

        document = self.env['irg.scholarship.document'].browse(result['document_id'])

        self.assertEqual(status, 200)
        self.assertTrue(result['ok'])
        self.assertEqual(result['action'], 'created')
        self.assertEqual(document.partner_id, self.partner)
        self.assertEqual(document.name, 'Solicitud de beca')
        self.assertEqual(document.filename, 'solicitud.pdf')

    def test_process_payload_assigns_scholarship_type_to_partner(self):
        result, status = self.service.process_payload(
            self._payload(scholarship_type_name=self.scholarship_type.name)
        )

        document = self.env['irg.scholarship.document'].browse(result['document_id'])

        self.assertEqual(status, 200)
        self.assertEqual(self.partner.irg_scholarship_type_id, self.scholarship_type)
        self.assertEqual(document.scholarship_type_id, self.scholarship_type)

    def test_process_payload_assigns_scholarship_type_by_key(self):
        result, status = self.service.process_payload(
            self._payload(scholarship_type_key='merito-academico')
        )

        self.assertEqual(status, 200)
        self.assertEqual(self.partner.irg_scholarship_type_id, self.scholarship_type)

    def test_process_payload_assigns_scholarship_type_without_accents(self):
        scholarship_type = self.env['op.scholarship.type'].create({
            'name': 'Beca Desocupación',
            'amount': 999,
        })

        result, status = self.service.process_payload(
            self._payload(scholarship_type_name='Beca Desocupacion')
        )

        self.assertEqual(status, 200)
        self.assertEqual(self.partner.irg_scholarship_type_id, scholarship_type)

    def test_process_payload_rejects_unknown_scholarship_type(self):
        result, status = self.service.process_payload(
            self._payload(scholarship_type_name='Beca inexistente')
        )

        self.assertEqual(status, 400)
        self.assertEqual(result['error'], 'scholarship_type_not_found')

    def test_process_payload_updates_existing_document(self):
        first_result, first_status = self.service.process_payload(self._payload(note='Primera nota'))
        second_result, second_status = self.service.process_payload(self._payload(note='Nota actualizada'))
        documents = self.env['irg.scholarship.document'].search([
            ('partner_id', '=', self.partner.id),
            ('filename', '=', 'solicitud.pdf'),
            ('name', '=', 'Solicitud de beca'),
        ])

        self.assertEqual(first_status, 200)
        self.assertEqual(second_status, 200)
        self.assertEqual(first_result['document_id'], second_result['document_id'])
        self.assertEqual(second_result['action'], 'updated')
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents.note, 'Nota actualizada')
