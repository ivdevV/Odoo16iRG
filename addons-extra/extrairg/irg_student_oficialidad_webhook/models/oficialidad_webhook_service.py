# -*- coding: utf-8 -*-

import base64
import binascii
import hmac
import os
import re

import psycopg2

from odoo import _, models

WEBHOOK_TOKEN_PARAM = 'irg_student_oficialidad_webhook.token'
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
# Longest base64 text that can decode to MAX_FILE_SIZE_BYTES (4 chars per 3 bytes).
MAX_BASE64_LENGTH = ((MAX_FILE_SIZE_BYTES + 2) // 3) * 4
ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
STUDENT_TYPES = ('nacional', 'internacional')
MAX_FILENAME_LENGTH = 255
MAX_NAME_LENGTH = 255
MAX_EMAIL_LENGTH = 254
MAX_DOCUMENT_TYPE_KEY_LENGTH = 64
MAX_NOTE_LENGTH = 2000

_CONTROL_CHARS_RE = re.compile(r'[\x00-\x1f\x7f-\x9f\u2028\u2029]')
_CONTROL_CHARS_KEEP_NEWLINES_RE = re.compile(
    r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\u2028\u2029]'
)


class IrgOficialidadWebhookService(models.AbstractModel):
    _name = 'irg.oficialidad.webhook.service'
    _description = 'Servicio de webhook para documentacion de oficialidad IRG'

    # ------------------------------------------------------------------
    # Authorization
    # ------------------------------------------------------------------
    def validate_authorization(self, authorization_header):
        """Return None when the Bearer token is valid, else an error dict.

        This is the only place that may run before the payload is validated
        and the only ``sudo`` it needs is reading the token parameter.
        """
        configured_token = self.env['ir.config_parameter'].sudo().get_param(
            WEBHOOK_TOKEN_PARAM
        )
        configured_token = (
            configured_token.strip() if isinstance(configured_token, str) else ''
        )
        if not configured_token:
            return {
                'ok': False,
                'error': 'webhook_token_not_configured',
                'message': _('El token del webhook no esta configurado.'),
            }

        prefix = 'Bearer '
        if not isinstance(authorization_header, str) or not authorization_header.startswith(prefix):
            return {
                'ok': False,
                'error': 'missing_token',
                'message': _('Falta la cabecera Authorization Bearer.'),
            }

        received_token = authorization_header[len(prefix):].strip()
        try:
            # Compare bytes: hmac.compare_digest raises TypeError on non-ASCII str.
            is_valid = hmac.compare_digest(
                received_token.encode('utf-8'),
                configured_token.encode('utf-8'),
            )
        except (TypeError, ValueError):  # UnicodeError is a ValueError
            is_valid = False
        if not is_valid:
            return {
                'ok': False,
                'error': 'invalid_token',
                'message': _('Token del webhook invalido.'),
            }
        return None

    # ------------------------------------------------------------------
    # Payload processing
    # ------------------------------------------------------------------
    def process_payload(self, payload):
        # Validation order (Security Advisor C3): object -> required fields and
        # student_type -> file -> document type/scope -> partner by email ->
        # sudo write. Nothing touches student data until everything else passed.
        if not isinstance(payload, dict):
            return self._error('invalid_payload', _('El payload debe ser un objeto JSON.'))

        email = self._clean_required_text(payload, 'email', MAX_EMAIL_LENGTH)
        raw_filename = self._clean_required_text(payload, 'filename')
        document_type_key = self._clean_required_text(
            payload, 'document_type_key', MAX_DOCUMENT_TYPE_KEY_LENGTH
        )
        encoded_file = payload.get('document_content_base64')
        if not email or not raw_filename or not document_type_key or not isinstance(encoded_file, str):
            return self._error(
                'missing_required_field',
                _('Los campos email, filename, document_content_base64 y document_type_key son obligatorios.'),
            )

        student_type = payload.get('student_type')
        student_type = student_type.strip() if isinstance(student_type, str) else False
        if student_type not in STUDENT_TYPES:
            return self._error(
                'invalid_student_type',
                _('student_type debe ser "nacional" o "internacional".'),
            )

        filename = self._sanitize_filename(raw_filename)
        file_content, error = self._read_file(filename, encoded_file.strip())
        if error:
            return error

        document_type, error = self._resolve_document_type(document_type_key, student_type)
        if error:
            return error

        document_name = (
            self._clean_optional_text(payload, 'document_name', MAX_NAME_LENGTH)
            or document_type.name
        )
        note = self._clean_optional_text(
            payload, 'note', MAX_NOTE_LENGTH, keep_newlines=True
        )

        partner, student, error = self._resolve_partner_by_email(email)
        if error:
            return error

        # The external application has no Odoo user; sudo is used only after
        # validating the shared token, payload, file, document type and target
        # partner.
        partner = partner.sudo()
        values = {
            'name': document_name,
            'filename': filename,
            'file': base64.b64encode(file_content),
            'note': note,
        }
        # The document is stored first; the partner's student type is written
        # only after that succeeded, inside one savepoint, so a failure can
        # never leave a changed student type without its document.
        with self.env.cr.savepoint():
            document, action = self._upsert_document(partner, document_type, values)
            if partner.irg_oficialidad_student_type != student_type:
                partner.write({'irg_oficialidad_student_type': student_type})

        return {
            'ok': True,
            'action': action,
            'document_id': document.id,
            'partner_id': partner.id,
            'student_id': student.id if student else False,
        }, 200

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _find_document(self, partner, document_type):
        return self.env['irg.oficialidad.document'].sudo().search([
            ('partner_id', '=', partner.id),
            ('document_type_id', '=', document_type.id),
        ], limit=1)

    def _upsert_document(self, partner, document_type, values):
        """Idempotent on (partner, document type). Returns (document, action)."""
        document_model = self.env['irg.oficialidad.document'].sudo()
        existing = self._find_document(partner, document_type)
        if existing:
            existing.write(values)
            return existing, 'updated'

        create_values = dict(values, partner_id=partner.id, document_type_id=document_type.id)
        try:
            with self.env.cr.savepoint():
                return document_model.create(create_values), 'created'
        except psycopg2.IntegrityError:
            # A concurrent request created the same (partner, type) first: the
            # UNIQUE constraint turned the race into an update.
            existing = self._find_document(partner, document_type)
            if not existing:
                raise
            existing.write(values)
            return existing, 'updated'

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _clean_required_text(payload, key, max_length=None):
        value = payload.get(key)
        if not isinstance(value, str):
            return False
        cleaned = _CONTROL_CHARS_RE.sub('', value).strip()
        return cleaned[:max_length] if max_length else cleaned

    @staticmethod
    def _clean_optional_text(payload, key, max_length, keep_newlines=False):
        value = payload.get(key)
        if not isinstance(value, str):
            return ''
        pattern = _CONTROL_CHARS_KEEP_NEWLINES_RE if keep_newlines else _CONTROL_CHARS_RE
        return pattern.sub('', value).strip()[:max_length]

    @staticmethod
    def _sanitize_filename(filename):
        """Untrusted client text: basename only, no control chars, bounded."""
        cleaned = _CONTROL_CHARS_RE.sub('', filename).replace('\\', '/')
        cleaned = os.path.basename(cleaned).strip()
        if len(cleaned) > MAX_FILENAME_LENGTH:
            stem, extension = os.path.splitext(cleaned)
            extension = extension[:16]
            cleaned = stem[:MAX_FILENAME_LENGTH - len(extension)] + extension
        return cleaned

    # ------------------------------------------------------------------
    # File
    # ------------------------------------------------------------------
    def _read_file(self, filename, encoded_file):
        # Cheap size check on the base64 text BEFORE decoding (DoS guard).
        if len(encoded_file) > MAX_BASE64_LENGTH:
            return None, self._file_too_large()
        try:
            file_content = base64.b64decode(encoded_file, validate=True)
        except (binascii.Error, ValueError):
            return None, self._error(
                'invalid_base64',
                _('El campo document_content_base64 no contiene base64 valido.'),
            )

        extension = os.path.splitext(filename)[1].lower()
        if extension not in ALLOWED_EXTENSIONS:
            return None, self._error(
                'invalid_file_extension',
                _('Formato no permitido. Usa PDF, JPG, PNG, DOC o DOCX.'),
            )
        if not file_content:
            return None, self._error('empty_file', _('El archivo esta vacio.'))
        if len(file_content) > MAX_FILE_SIZE_BYTES:
            return None, self._file_too_large()
        return file_content, None

    def _file_too_large(self):
        return self._error(
            'file_too_large',
            _('El archivo supera el limite de 10 MB.'),
            status=413,
        )

    # ------------------------------------------------------------------
    # Document type
    # ------------------------------------------------------------------
    def _resolve_document_type(self, document_type_key, student_type):
        # sudo: reads only the public catalogue of document types.
        document_types = self.env['irg.oficialidad.document.type'].sudo().search([
            ('key', '=', document_type_key),
            ('active', '=', True),
        ])
        if len(document_types) > 1:
            return False, self._error(
                'ambiguous_document_type',
                _('Hay mas de un tipo de documento con la clave indicada.'),
                status=409,
            )
        if not document_types:
            return False, self._error(
                'document_type_not_found',
                _('No se encontro ningun tipo de documento con la clave indicada.'),
                status=404,
            )
        if document_types.student_type_scope not in ('both', student_type):
            return False, self._error(
                'document_type_student_type_mismatch',
                _('El tipo de documento no corresponde al tipo de alumno indicado.'),
                status=409,
            )
        return document_types, None

    # ------------------------------------------------------------------
    # Partner
    # ------------------------------------------------------------------
    @staticmethod
    def _escape_like(value):
        """Escape ilike wildcards so the email is matched literally."""
        return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')

    def _resolve_partner_by_email(self, email):
        escaped_email = self._escape_like(email.strip().lower())
        student_model = self.env['op.student'].sudo()
        students = student_model.search([('partner_id.email', '=ilike', escaped_email)])
        if len(students) > 1:
            error, status = self._error(
                'ambiguous_email',
                _('Hay mas de un alumno con el email indicado.'),
                status=409,
            )
            return None, None, (error, status)
        if students:
            return students.partner_id, students, None

        partners = self.env['res.partner'].sudo().search([('email', '=ilike', escaped_email)])
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

    @staticmethod
    def _error(error, message, status=400):
        return {
            'ok': False,
            'error': error,
            'message': message,
        }, status
