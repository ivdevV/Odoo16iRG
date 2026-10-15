# -*- coding: utf-8 -*-

import base64
import json
import logging
from unittest import mock

from odoo.tests import tagged
from odoo.tests.common import HttpCase, TransactionCase

TOKEN_PARAM = 'irg_student_oficialidad_webhook.token'
TEST_TOKEN = 'test-token-ephemeral'
SERVICE_MODULE = (
    'odoo.addons.irg_student_oficialidad_webhook.models.'
    'oficialidad_webhook_service'
)


class OficialidadWebhookCommon(object):
    def _setup_fixtures(self):
        self.service = self.env['irg.oficialidad.webhook.service'].sudo()
        self.env['ir.config_parameter'].sudo().set_param(TOKEN_PARAM, TEST_TOKEN)
        self.partner = self.env['res.partner'].create({
            'name': 'Alumno Oficialidad Webhook',
            'email': 'alumno.oficialidad@example.com',
        })
        self.document_model = self.env['irg.oficialidad.document']

    def _payload(self, **overrides):
        payload = {
            'email': self.partner.email,
            'filename': 'titulo.pdf',
            'document_name': 'Titulo universitario',
            'document_type_key': 'titulo-universitario',
            'document_content_base64': base64.b64encode(b'%PDF-1.4 x').decode('ascii'),
            'student_type': 'nacional',
            'student_type_name': 'Alumno nacional',
            'note': 'Recibido desde la app de oficialidad',
        }
        payload.update(overrides)
        return payload


@tagged('post_install', '-at_install')
class TestOficialidadWebhookAuth(OficialidadWebhookCommon, TransactionCase):
    def setUp(self):
        super().setUp()
        self._setup_fixtures()

    def test_authorization_missing_header(self):
        result = self.service.validate_authorization(None)
        self.assertEqual(result['error'], 'missing_token')

    def test_authorization_without_bearer_prefix(self):
        result = self.service.validate_authorization(TEST_TOKEN)
        self.assertEqual(result['error'], 'missing_token')

    def test_authorization_invalid_token(self):
        result = self.service.validate_authorization('Bearer wrong-token')
        self.assertEqual(result['error'], 'invalid_token')

    def test_authorization_empty_bearer_value(self):
        result = self.service.validate_authorization('Bearer ')
        self.assertEqual(result['error'], 'invalid_token')

    def test_authorization_valid_token(self):
        self.assertIsNone(
            self.service.validate_authorization('Bearer %s' % TEST_TOKEN)
        )

    def test_authorization_non_ascii_token_is_invalid_not_exception(self):
        # C1: hmac.compare_digest on str raises TypeError for non-ASCII.
        for header in ('Bearer ñandú', 'Bearer \u20ac\u20ac', 'Bearer \ud800'):
            result = self.service.validate_authorization(header)
            self.assertEqual(result['error'], 'invalid_token', header)

    def test_authorization_non_ascii_configured_token_still_works(self):
        self.env['ir.config_parameter'].sudo().set_param(TOKEN_PARAM, 'tökén-ñ')
        self.assertIsNone(self.service.validate_authorization('Bearer tökén-ñ'))
        result = self.service.validate_authorization('Bearer token-n')
        self.assertEqual(result['error'], 'invalid_token')

    def test_authorization_unconfigured_token_fails_closed(self):
        # C2: empty / whitespace / missing parameter == not configured.
        param = self.env['ir.config_parameter'].sudo()
        for value in ('', '   ', '\t\n'):
            param.set_param(TOKEN_PARAM, value)
            for header in ('Bearer ', 'Bearer x', 'Bearer    ', None):
                result = self.service.validate_authorization(header)
                self.assertEqual(
                    result['error'], 'webhook_token_not_configured', (value, header)
                )
        param.search([('key', '=', TOKEN_PARAM)]).unlink()
        result = self.service.validate_authorization('Bearer x')
        self.assertEqual(result['error'], 'webhook_token_not_configured')

    def test_authorization_messages_do_not_leak_token(self):
        for header in (None, 'Bearer wrong-token'):
            result = self.service.validate_authorization(header)
            self.assertNotIn(TEST_TOKEN, json.dumps(result))
            self.assertNotIn('wrong-token', json.dumps(result))


@tagged('post_install', '-at_install')
class TestOficialidadWebhookPayload(OficialidadWebhookCommon, TransactionCase):
    def setUp(self):
        super().setUp()
        self._setup_fixtures()

    # -- structure / required fields ---------------------------------------

    def test_payload_must_be_object(self):
        for payload in ([], 'text', None, 7):
            result, status = self.service.process_payload(payload)
            self.assertEqual(status, 400)
            self.assertEqual(result['error'], 'invalid_payload')

    def test_missing_required_fields(self):
        for key in ('email', 'filename', 'document_type_key'):
            for bad in ('', '   ', None, 123):
                result, status = self.service.process_payload(self._payload(**{key: bad}))
                self.assertEqual(status, 400, (key, bad))
                self.assertEqual(result['error'], 'missing_required_field', (key, bad))
        for bad in (None, 123, ['x']):
            result, status = self.service.process_payload(
                self._payload(document_content_base64=bad)
            )
            self.assertEqual(status, 400, bad)
            self.assertEqual(result['error'], 'missing_required_field', bad)

    def test_missing_or_invalid_student_type(self):
        payload = self._payload()
        payload.pop('student_type')
        result, status = self.service.process_payload(payload)
        self.assertEqual(status, 400)
        self.assertEqual(result['error'], 'invalid_student_type')

        for bad in ('', 'extranjero', 'NACIONAL', None, 5, ['nacional']):
            result, status = self.service.process_payload(self._payload(student_type=bad))
            self.assertEqual(status, 400, bad)
            self.assertEqual(result['error'], 'invalid_student_type', bad)

    def test_student_type_is_trimmed(self):
        result, status = self.service.process_payload(
            self._payload(student_type=' nacional ')
        )
        self.assertEqual(status, 200)
        self.assertEqual(self.partner.irg_oficialidad_student_type, 'nacional')

    # -- document type -----------------------------------------------------

    def test_unknown_document_type_key(self):
        result, status = self.service.process_payload(
            self._payload(document_type_key='no-existe')
        )
        self.assertEqual(status, 404)
        self.assertEqual(result['error'], 'document_type_not_found')

    def test_inactive_document_type_not_found(self):
        self.env['irg.oficialidad.document.type'].search(
            [('key', '=', 'titulo-universitario')]
        ).write({'active': False})
        result, status = self.service.process_payload(self._payload())
        self.assertEqual(status, 404)
        self.assertEqual(result['error'], 'document_type_not_found')

    def test_apostillado_with_nacional_is_mismatch(self):
        result, status = self.service.process_payload(self._payload(
            document_type_key='titulo-universitario-apostillado',
            student_type='nacional',
        ))
        self.assertEqual(status, 409)
        self.assertEqual(result['error'], 'document_type_student_type_mismatch')
        self.assertFalse(self.partner.irg_oficialidad_student_type)
        self.assertFalse(self.document_model.search([('partner_id', '=', self.partner.id)]))

    def test_nacional_type_with_internacional_student_is_mismatch(self):
        result, status = self.service.process_payload(self._payload(
            document_type_key='titulo-universitario',
            student_type='internacional',
        ))
        self.assertEqual(status, 409)
        self.assertEqual(result['error'], 'document_type_student_type_mismatch')

    def test_both_scope_type_accepted_for_either_student_type(self):
        for student_type in ('nacional', 'internacional'):
            partner = self.env['res.partner'].create({
                'name': 'Alumno %s' % student_type,
                'email': 'both.%s@example.com' % student_type,
            })
            result, status = self.service.process_payload(self._payload(
                email=partner.email,
                document_type_key='matricula-unimarconi',
                student_type=student_type,
            ))
            self.assertEqual(status, 200, student_type)
            self.assertEqual(partner.irg_oficialidad_student_type, student_type)

    # -- partner resolution ------------------------------------------------

    def test_unknown_email(self):
        result, status = self.service.process_payload(
            self._payload(email='missing@example.com')
        )
        self.assertEqual(status, 404)
        self.assertEqual(result['error'], 'partner_not_found')

    def test_ambiguous_partner_email(self):
        self.env['res.partner'].create({
            'name': 'Duplicado',
            'email': self.partner.email,
        })
        result, status = self.service.process_payload(self._payload())
        self.assertEqual(status, 409)
        self.assertEqual(result['error'], 'ambiguous_email')
        self.assertFalse(self.document_model.search([('partner_id', '=', self.partner.id)]))

    def test_email_lookup_is_case_insensitive(self):
        result, status = self.service.process_payload(
            self._payload(email='  ALUMNO.Oficialidad@Example.COM ')
        )
        self.assertEqual(status, 200)
        self.assertEqual(result['partner_id'], self.partner.id)

    def test_email_wildcards_are_not_expanded(self):
        # C4: '%' / '_' must not behave as ilike wildcards.
        self.env['res.partner'].create({
            'name': 'Otro Alumno',
            'email': 'otro.alumno@example.com',
        })
        for email in ('%', '%@example.com', 'alumno_oficialidad@example.com',
                      'alumno.oficialidad@example.co_', 'a%'):
            result, status = self.service.process_payload(self._payload(email=email))
            self.assertEqual(status, 404, email)
            self.assertEqual(result['error'], 'partner_not_found', email)
        self.assertFalse(self.document_model.search([]))

    def test_email_backslash_is_not_an_escape(self):
        result, status = self.service.process_payload(
            self._payload(email='alumno.oficialidad\\@example.com')
        )
        self.assertEqual(status, 404)
        self.assertEqual(result['error'], 'partner_not_found')

    def test_resolves_student_by_email(self):
        student_partner = self.env['res.partner'].create({
            'name': 'Alumno Con Ficha',
            'email': 'ficha.oficialidad@example.com',
        })
        student = self.env['op.student'].create({
            'partner_id': student_partner.id,
            'first_name': 'Alumno',
            'last_name': 'Con Ficha',
            'birth_date': '2000-01-01',
            'gender': 'm',
        })
        result, status = self.service.process_payload(
            self._payload(email='ficha.oficialidad@example.com')
        )
        self.assertEqual(status, 200)
        self.assertEqual(result['student_id'], student.id)
        self.assertEqual(result['partner_id'], student.partner_id.id)

    # -- file validation ---------------------------------------------------

    def test_invalid_base64(self):
        result, status = self.service.process_payload(
            self._payload(document_content_base64='not-valid-base64')
        )
        self.assertEqual(status, 400)
        self.assertEqual(result['error'], 'invalid_base64')

    def test_invalid_extension(self):
        for filename in ('titulo.exe', 'titulo', 'titulo.pdf.exe', '.pdf'):
            result, status = self.service.process_payload(self._payload(filename=filename))
            self.assertEqual(status, 400, filename)
            self.assertEqual(result['error'], 'invalid_file_extension', filename)

    def test_empty_file(self):
        for content in ('', base64.b64encode(b'').decode('ascii'), '   '):
            result, status = self.service.process_payload(
                self._payload(document_content_base64=content)
            )
            self.assertEqual(status, 400, repr(content))
            self.assertEqual(result['error'], 'empty_file', repr(content))

    def test_padding_only_base64_is_invalid(self):
        # '====' decodes (non-strict) to nothing but is invalid under validate=True.
        result, status = self.service.process_payload(
            self._payload(document_content_base64='====')
        )
        self.assertEqual(status, 400)
        self.assertEqual(result['error'], 'invalid_base64')

    def test_file_too_large_decoded(self):
        from odoo.addons.irg_student_oficialidad_webhook.models import (
            oficialidad_webhook_service as module,
        )
        content = base64.b64encode(b'a' * (module.MAX_FILE_SIZE_BYTES + 1)).decode('ascii')
        result, status = self.service.process_payload(
            self._payload(document_content_base64=content)
        )
        self.assertEqual(status, 413)
        self.assertEqual(result['error'], 'file_too_large')

    def test_oversized_base64_rejected_before_decode(self):
        # C3/C9: length check precedes base64 decoding.
        from odoo.addons.irg_student_oficialidad_webhook.models import (
            oficialidad_webhook_service as module,
        )
        huge = 'A' * (module.MAX_BASE64_LENGTH + 4)
        with mock.patch(SERVICE_MODULE + '.base64.b64decode') as decode:
            result, status = self.service.process_payload(
                self._payload(document_content_base64=huge)
            )
        decode.assert_not_called()
        self.assertEqual(status, 413)
        self.assertEqual(result['error'], 'file_too_large')

    def test_exact_limit_file_accepted(self):
        from odoo.addons.irg_student_oficialidad_webhook.models import (
            oficialidad_webhook_service as module,
        )
        content = base64.b64encode(b'a' * module.MAX_FILE_SIZE_BYTES).decode('ascii')
        self.assertLessEqual(len(content), module.MAX_BASE64_LENGTH)
        result, status = self.service.process_payload(
            self._payload(document_content_base64=content)
        )
        self.assertEqual(status, 200)

    # -- ordering (C3) -----------------------------------------------------

    def test_file_validated_before_email_lookup(self):
        # Invalid file + unknown email must report the file error, not
        # partner_not_found (no email existence oracle with bad payloads).
        result, status = self.service.process_payload(self._payload(
            email='missing@example.com',
            filename='titulo.exe',
        ))
        self.assertEqual(result['error'], 'invalid_file_extension')

    def test_document_type_validated_before_email_lookup(self):
        result, status = self.service.process_payload(self._payload(
            email='missing@example.com',
            document_type_key='no-existe',
        ))
        self.assertEqual(result['error'], 'document_type_not_found')

    def test_student_type_validated_before_file_and_email(self):
        result, status = self.service.process_payload(self._payload(
            email='missing@example.com',
            filename='titulo.exe',
            student_type='otro',
        ))
        self.assertEqual(result['error'], 'invalid_student_type')

    def test_no_email_search_before_validation_passes(self):
        student_model = type(self.env['op.student'])
        partner_model = type(self.env['res.partner'])
        with mock.patch.object(student_model, 'search') as s_search, \
                mock.patch.object(partner_model, 'search') as p_search:
            self.service.process_payload(self._payload(filename='titulo.exe'))
            self.service.process_payload(self._payload(document_type_key='no-existe'))
            self.service.process_payload(self._payload(student_type='x'))
        s_search.assert_not_called()
        p_search.assert_not_called()

    # -- filename sanitising (C5) -----------------------------------------

    def _stored_filename(self, result):
        return self.document_model.browse(result['document_id']).filename

    def test_filename_path_components_stripped(self):
        for raw in ('../../etc/passwd.pdf', '/tmp/evil/titulo.pdf',
                    'C:\\Users\\x\\titulo.pdf', 'a/b\\c/titulo.pdf'):
            self.document_model.search([]).unlink()
            result, status = self.service.process_payload(self._payload(filename=raw))
            self.assertEqual(status, 200, raw)
            stored = self._stored_filename(result)
            self.assertNotIn('/', stored)
            self.assertNotIn('\\', stored)
            self.assertTrue(stored.endswith('.pdf'), stored)

    def test_filename_control_characters_removed(self):
        result, status = self.service.process_payload(
            self._payload(filename='ti\x00tu\x1blo\r\n.pdf')
        )
        self.assertEqual(status, 200)
        self.assertEqual(self._stored_filename(result), 'titulo.pdf')

    def test_filename_length_limited_keeping_extension(self):
        result, status = self.service.process_payload(
            self._payload(filename=('x' * 600) + '.pdf')
        )
        self.assertEqual(status, 200)
        stored = self._stored_filename(result)
        self.assertLessEqual(len(stored), 255)
        self.assertTrue(stored.endswith('.pdf'))

    def test_document_name_and_note_sanitised_and_bounded(self):
        result, status = self.service.process_payload(self._payload(
            document_name='Ti\x00tulo ' + 'n' * 600,
            note='Nota\x00 ' + 'z' * 5000,
        ))
        self.assertEqual(status, 200)
        document = self.document_model.browse(result['document_id'])
        self.assertNotIn('\x00', document.name)
        self.assertLessEqual(len(document.name), 255)
        self.assertNotIn('\x00', document.note)
        self.assertLessEqual(len(document.note), 2000)

    def test_document_name_defaults_to_type_name(self):
        result, status = self.service.process_payload(self._payload(document_name=''))
        self.assertEqual(status, 200)
        document = self.document_model.browse(result['document_id'])
        self.assertEqual(document.name, document.document_type_id.name)

    # -- persistence / idempotence (C6, C7) --------------------------------

    def test_creates_document_and_persists_student_type(self):
        result, status = self.service.process_payload(self._payload())
        document = self.document_model.browse(result['document_id'])
        self.assertEqual(status, 200)
        self.assertTrue(result['ok'])
        self.assertEqual(result['action'], 'created')
        self.assertEqual(document.partner_id, self.partner)
        self.assertEqual(document.document_type_id.key, 'titulo-universitario')
        self.assertEqual(document.name, 'Titulo universitario')
        self.assertEqual(document.filename, 'titulo.pdf')
        self.assertEqual(document.note, 'Recibido desde la app de oficialidad')
        self.assertEqual(base64.b64decode(document.file), b'%PDF-1.4 x')
        self.assertEqual(self.partner.irg_oficialidad_student_type, 'nacional')
        self.assertFalse(result['student_id'])
        self.assertEqual(set(result), {'ok', 'action', 'document_id', 'partner_id', 'student_id'})

    def test_same_type_again_updates(self):
        first, first_status = self.service.process_payload(self._payload(note='Primera'))
        second, second_status = self.service.process_payload(self._payload(
            note='Actualizada',
            filename='titulo_v2.pdf',
            document_content_base64=base64.b64encode(b'%PDF-1.4 v2').decode('ascii'),
        ))
        documents = self.document_model.search([('partner_id', '=', self.partner.id)])
        self.assertEqual((first_status, second_status), (200, 200))
        self.assertEqual(first['action'], 'created')
        self.assertEqual(second['action'], 'updated')
        self.assertEqual(first['document_id'], second['document_id'])
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents.note, 'Actualizada')
        self.assertEqual(documents.filename, 'titulo_v2.pdf')
        self.assertEqual(base64.b64decode(documents.file), b'%PDF-1.4 v2')

    def test_different_types_create_distinct_documents(self):
        self.service.process_payload(self._payload())
        result, status = self.service.process_payload(self._payload(
            document_type_key='certificado-notas',
            filename='notas.pdf',
        ))
        self.assertEqual(result['action'], 'created')
        self.assertEqual(
            len(self.document_model.search([('partner_id', '=', self.partner.id)])), 2
        )

    def test_student_type_updated_on_later_document(self):
        self.service.process_payload(self._payload())
        self.assertEqual(self.partner.irg_oficialidad_student_type, 'nacional')
        result, status = self.service.process_payload(self._payload(
            document_type_key='pasaporte',
            student_type='internacional',
            filename='pasaporte.pdf',
        ))
        self.assertEqual(status, 200)
        self.assertEqual(self.partner.irg_oficialidad_student_type, 'internacional')

    def test_rejected_payload_does_not_change_student_type(self):
        self.partner.sudo().write({'irg_oficialidad_student_type': 'nacional'})
        result, status = self.service.process_payload(self._payload(
            document_type_key='pasaporte',
            student_type='internacional',
            filename='pasaporte.exe',
        ))
        self.assertEqual(status, 400)
        self.assertEqual(self.partner.irg_oficialidad_student_type, 'nacional')

    def test_upsert_failure_does_not_change_partner_student_type(self):
        # With the old order the partner was written before the upsert, so a
        # generic failure left a changed student type without a document.
        self.partner.sudo().write({'irg_oficialidad_student_type': 'nacional'})
        service_cls = type(self.service)
        # NB: do not use assertRaises here: Odoo's wrapper runs the block in a
        # savepoint and would hide a partner write that leaked.
        with mock.patch.object(
            service_cls, '_upsert_document', side_effect=RuntimeError('boom')
        ):
            try:
                self.service.process_payload(self._payload(
                    document_type_key='pasaporte',
                    student_type='internacional',
                    filename='pasaporte.pdf',
                ))
            except RuntimeError:
                pass
            else:
                self.fail('RuntimeError was not propagated')
        self.assertEqual(self.partner.irg_oficialidad_student_type, 'nacional')

    def test_partner_write_failure_rolls_back_created_document(self):
        partner_cls = type(self.env['res.partner'])
        with mock.patch.object(partner_cls, 'write', side_effect=RuntimeError('boom')):
            try:
                self.service.process_payload(self._payload())
            except RuntimeError:
                pass
            else:
                self.fail('RuntimeError was not propagated')
        self.assertFalse(self.document_model.search([('partner_id', '=', self.partner.id)]))

    def test_student_type_written_after_document_exists(self):
        self.service.process_payload(self._payload())
        self.assertEqual(self.partner.irg_oficialidad_student_type, 'nacional')
        self.assertTrue(self.document_model.search([('partner_id', '=', self.partner.id)]))

    def test_control_chars_stripped_from_email_and_type_key(self):
        result, status = self.service.process_payload(self._payload(
            email='alumno.oficialidad\x00@example.com\r\n',
            document_type_key='titulo-\x00universitario\x1b',
        ))
        self.assertEqual(status, 200)
        self.assertEqual(result['partner_id'], self.partner.id)

    def test_overlong_email_and_type_key_are_bounded(self):
        result, status = self.service.process_payload(
            self._payload(email=('a' * 400) + '@example.com')
        )
        self.assertEqual(status, 404)
        self.assertEqual(result['error'], 'partner_not_found')
        result, status = self.service.process_payload(
            self._payload(document_type_key='k' * 5000)
        )
        self.assertEqual(status, 404)
        self.assertEqual(result['error'], 'document_type_not_found')

    def test_concurrent_create_race_falls_back_to_update(self):
        # C6: a lost race on UNIQUE(partner_id, document_type_id) becomes an update.
        first, _status = self.service.process_payload(self._payload(note='Primera'))
        service_cls = type(self.service)
        empty = self.document_model.browse()
        existing = self.document_model.browse(first['document_id'])
        with mock.patch.object(
            service_cls, '_find_document', side_effect=[empty, existing]
        ):
            second, status = self.service.process_payload(self._payload(note='Carrera'))
        self.assertEqual(status, 200)
        self.assertEqual(second['action'], 'updated')
        self.assertEqual(second['document_id'], first['document_id'])
        self.assertEqual(existing.note, 'Carrera')
        self.assertEqual(
            len(self.document_model.search([('partner_id', '=', self.partner.id)])), 1
        )

    def test_attachment_is_private(self):
        # C7/C9: PII attachment must never be public.
        result, status = self.service.process_payload(self._payload())
        self.env.flush_all()
        attachments = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'irg.oficialidad.document'),
            ('res_field', '=', 'file'),
            ('res_id', '=', result['document_id']),
        ])
        self.assertTrue(attachments)
        self.assertFalse(any(attachments.mapped('public')))

    def test_attachment_stays_private_after_update(self):
        first, _status = self.service.process_payload(self._payload())
        self.service.process_payload(self._payload(
            document_content_base64=base64.b64encode(b'%PDF-1.4 v2').decode('ascii'),
        ))
        self.env.flush_all()
        attachments = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'irg.oficialidad.document'),
            ('res_field', '=', 'file'),
            ('res_id', '=', first['document_id']),
        ])
        self.assertTrue(attachments)
        self.assertFalse(any(attachments.mapped('public')))

    # -- VAT hint never blocks --------------------------------------------

    def test_type_mismatch_vat_does_not_block(self):
        # DNI-looking VAT but the app says internacional: accepted, flagged only.
        self.partner.sudo().write({'vat': '12345678Z'})
        result, status = self.service.process_payload(self._payload(
            document_type_key='pasaporte',
            student_type='internacional',
            filename='pasaporte.pdf',
        ))
        self.assertEqual(status, 200)
        self.assertEqual(self.partner.irg_oficialidad_student_type, 'internacional')
        self.assertTrue(self.partner.irg_oficialidad_type_mismatch)

    def test_service_does_not_leak_payload_in_logs(self):
        # C8: the service must not log email, token or file content. Odoo's own
        # DEBUG SQL logging is framework behaviour, so capture INFO and above.
        records = []
        handler = logging.Handler(level=logging.INFO)
        handler.emit = records.append
        root = logging.getLogger()
        root.addHandler(handler)
        try:
            self.service.process_payload(self._payload(email='missing@example.com'))
            self.service.process_payload(self._payload())
            self.service.validate_authorization('Bearer wrong-token')
        finally:
            root.removeHandler(handler)
        joined = '\n'.join(record.getMessage() for record in records)
        for secret in ('missing@example.com', self.partner.email, TEST_TOKEN,
                       'wrong-token', 'JVBERi'):
            self.assertNotIn(secret, joined)


@tagged('post_install', '-at_install')
class TestOficialidadWebhookHttp(OficialidadWebhookCommon, HttpCase):
    ROUTE = '/irg/oficialidad/webhook/document'

    def setUp(self):
        super().setUp()
        self._setup_fixtures()
        # Anonymous session bound to the test database (no user login): the
        # route is auth='none', so only the db must be resolvable.
        self.authenticate(None, None)

    def _post(self, payload=None, token=TEST_TOKEN, raw=None, headers=None):
        request_headers = {'Content-Type': 'application/json'}
        if token is not None:
            request_headers['Authorization'] = 'Bearer %s' % token
        request_headers.update(headers or {})
        body = raw if raw is not None else json.dumps(payload)
        return self.url_open(self.ROUTE, data=body, headers=request_headers)

    def test_missing_token_401(self):
        response = self._post(self._payload(), token=None)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'missing_token')

    def test_invalid_token_401(self):
        response = self._post(self._payload(), token='nope')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'invalid_token')

    def test_non_ascii_token_401_not_500(self):
        response = self._post(self._payload(), headers={
            'Authorization': 'Bearer ñandú'.encode('latin-1'),
        })
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'invalid_token')

    def test_unconfigured_token_401(self):
        self.env['ir.config_parameter'].sudo().set_param(TOKEN_PARAM, '')
        response = self._post(self._payload(), token='')
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error'], 'webhook_token_not_configured')

    def test_get_not_allowed(self):
        response = self.url_open(self.ROUTE)
        self.assertIn(response.status_code, (404, 405))

    def test_invalid_json_400(self):
        response = self._post(raw='{not json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'invalid_json')

    def test_non_object_json_400(self):
        response = self._post(raw='[1, 2]')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error'], 'invalid_payload')

    def test_oversized_body_413_before_parsing(self):
        # Not valid JSON: a 400 invalid_json would mean we parsed it first.
        response = self._post(raw='x' * (15 * 1024 * 1024 + 1))
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()['error'], 'file_too_large')

    def test_oversized_body_with_bad_token_is_401(self):
        response = self._post(raw='x' * (15 * 1024 * 1024 + 1), token='nope')
        self.assertEqual(response.status_code, 401)

    def test_success_end_to_end(self):
        response = self._post(self._payload())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['ok'])
        self.assertEqual(body['action'], 'created')
        again = self._post(self._payload())
        self.assertEqual(again.json()['action'], 'updated')
        self.assertEqual(again.json()['document_id'], body['document_id'])

    def test_unexpected_error_is_generic_500_without_leaks(self):
        service_cls = type(self.env['irg.oficialidad.webhook.service'])
        secret_email = self.partner.email
        with mock.patch.object(
            service_cls, 'process_payload',
            side_effect=Exception('boom %s %s' % ('internal-detail', TEST_TOKEN)),
        ), self.assertLogs('odoo.addons.irg_student_oficialidad_webhook', level='ERROR') as logs:
            response = self._post(self._payload())
        self.assertEqual(response.status_code, 500)
        body = response.json()
        self.assertEqual(body['error'], 'server_error')
        self.assertNotIn('internal-detail', response.text)
        self.assertNotIn(TEST_TOKEN, response.text)
        joined = '\n'.join(logs.output)
        self.assertNotIn(TEST_TOKEN, joined)
        self.assertNotIn(secret_email, joined)
        self.assertNotIn('JVBERi', joined)
