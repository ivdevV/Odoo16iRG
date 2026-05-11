# -*- coding: utf-8 -*-

import base64
import binascii
import hmac
import os
import re
import unicodedata

from odoo import _, models


WEBHOOK_TOKEN_PARAM = 'irg_student_scholarship_webhook.token'
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}


class IrgScholarshipWebhookService(models.AbstractModel):
    _name = 'irg.scholarship.webhook.service'
    _description = 'Servicio de webhook para documentacion de becas IRG'

    def validate_authorization(self, authorization_header):
        configured_token = self.env['ir.config_parameter'].sudo().get_param(
            WEBHOOK_TOKEN_PARAM
        )
        if not configured_token:
            return {
                'ok': False,
                'error': 'webhook_token_not_configured',
                'message': _('El token del webhook no esta configurado.'),
            }

        prefix = 'Bearer '
        if not authorization_header or not authorization_header.startswith(prefix):
            return {
                'ok': False,
                'error': 'missing_token',
                'message': _('Falta la cabecera Authorization Bearer.'),
            }

        received_token = authorization_header[len(prefix):].strip()
        if not hmac.compare_digest(received_token, configured_token):
            return {
                'ok': False,
                'error': 'invalid_token',
                'message': _('Token del webhook invalido.'),
            }
        return None

    def process_payload(self, payload):
        if not isinstance(payload, dict):
            return self._error('invalid_payload', _('El payload debe ser un objeto JSON.'))

        email = self._clean_required_text(payload, 'email')
        filename = self._clean_required_text(payload, 'filename')
        encoded_file = payload.get('document_content_base64')
        if not email or not filename or not isinstance(encoded_file, str):
            return self._error(
                'missing_required_field',
                _('Los campos email, filename y document_content_base64 son obligatorios.'),
            )
        encoded_file = encoded_file.strip()

        document_name = self._clean_optional_text(payload, 'document_name') or filename
        scholarship_type_key = self._clean_optional_text(payload, 'scholarship_type_key')
        scholarship_type_name = self._clean_optional_text(payload, 'scholarship_type_name')
        note = self._clean_optional_text(payload, 'note')

        partner, student, error = self._resolve_partner_by_email(email)
        if error:
            return error

        scholarship_type = False
        if scholarship_type_key or scholarship_type_name:
            scholarship_type, error = self._resolve_scholarship_type(
                scholarship_type_key,
                scholarship_type_name,
            )
            if error:
                return error

        file_content, error = self._decode_file(encoded_file)
        if error:
            return error

        error = self._validate_file(filename, file_content)
        if error:
            return error

        if scholarship_type and partner.irg_scholarship_type_id != scholarship_type:
            partner.sudo().write({'irg_scholarship_type_id': scholarship_type.id})

        document_model = self.env['irg.scholarship.document'].sudo()
        existing_document = document_model.search([
            ('partner_id', '=', partner.id),
            ('filename', '=', filename),
            ('name', '=', document_name),
        ], limit=1)
        values = {
            'partner_id': partner.id,
            'name': document_name,
            'filename': filename,
            'file': base64.b64encode(file_content),
            'note': note,
        }
        # The external application has no Odoo user; sudo is used only after
        # validating the shared token, payload, target partner and file content.
        if existing_document:
            existing_document.write(values)
            document = existing_document
            action = 'updated'
        else:
            document = document_model.create(values)
            action = 'created'

        return {
            'ok': True,
            'action': action,
            'document_id': document.id,
            'partner_id': partner.id,
            'student_id': student.id if student else False,
        }, 200

    @staticmethod
    def _clean_required_text(payload, key):
        value = payload.get(key)
        return value.strip() if isinstance(value, str) else False

    @staticmethod
    def _clean_optional_text(payload, key):
        value = payload.get(key)
        return value.strip() if isinstance(value, str) else ''

    def _resolve_partner_by_email(self, email):
        normalized_email = email.strip().lower()
        student_model = self.env['op.student'].sudo()
        students = student_model.search([('partner_id.email', '=ilike', normalized_email)])
        if len(students) > 1:
            error, status = self._error(
                'ambiguous_email',
                _('Hay mas de un alumno con el email indicado.'),
                status=409,
            )
            return None, None, (error, status)
        if students:
            return students.partner_id, students, None

        partners = self.env['res.partner'].sudo().search([('email', '=ilike', normalized_email)])
        if len(partners) > 1:
            error, status = self._error(
                'ambiguous_email',
                _('Hay mas de un contacto con el email indicado.'),
                status=409,
            )
            return None, None, (error, status)
        if not partners:
            error, status = self._error(
                'partner_not_found',
                _('No se encontro ningun alumno o contacto con el email indicado.'),
                status=404,
            )
            return None, None, (error, status)
        return partners, student_model.browse(), None

    def _resolve_scholarship_type(self, scholarship_type_key, scholarship_type_name):
        requested_keys = set()
        if scholarship_type_key:
            requested_keys.add(self._normalize_identifier(scholarship_type_key))
        if scholarship_type_name:
            requested_keys.add(self._normalize_identifier(scholarship_type_name))

        scholarship_types = self.env['op.scholarship.type'].sudo().search([
            ('active', '=', True),
        ])
        scholarship_types = scholarship_types.filtered(
            lambda scholarship_type: requested_keys.intersection(
                self._scholarship_type_identifiers(scholarship_type)
            )
        )
        if len(scholarship_types) > 1:
            return False, self._error(
                'ambiguous_scholarship_type',
                _('Hay mas de un tipo de beca con el nombre indicado.'),
                status=409,
            )
        if not scholarship_types:
            return False, self._error(
                'scholarship_type_not_found',
                _('No se encontro ningun tipo de beca con el nombre indicado.'),
            )
        return scholarship_types, None

    def _scholarship_type_identifiers(self, scholarship_type):
        identifiers = set()
        names = {
            scholarship_type.name,
            scholarship_type.with_context(lang=None).name,
        }
        for name in names:
            normalized_name = self._normalize_identifier(name)
            identifiers.add(normalized_name)
            if normalized_name.startswith('beca-'):
                identifiers.add(normalized_name[5:])
        return identifiers

    @staticmethod
    def _normalize_identifier(value):
        normalized = unicodedata.normalize('NFKD', value or '')
        ascii_value = ''.join(
            character for character in normalized
            if not unicodedata.combining(character)
        )
        return re.sub(r'[^a-z0-9]+', '-', ascii_value.lower()).strip('-')

    def _decode_file(self, encoded_file):
        try:
            return base64.b64decode(encoded_file, validate=True), None
        except (binascii.Error, ValueError):
            return None, self._error(
                'invalid_base64',
                _('El campo document_content_base64 no contiene base64 valido.'),
            )

    def _validate_file(self, filename, file_content):
        extension = os.path.splitext(filename)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            return self._error(
                'invalid_file_extension',
                _('Formato no permitido. Usa PDF, JPG, PNG, DOC o DOCX.'),
            )
        if not file_content:
            return self._error('empty_file', _('El archivo esta vacio.'))
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            return self._error(
                'file_too_large',
                _('El archivo supera el limite de 10 MB.'),
                status=413,
            )
        return None

    @staticmethod
    def _error(error, message, status=400):
        return {
            'ok': False,
            'error': error,
            'message': message,
        }, status
