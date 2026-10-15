# -*- coding: utf-8 -*-

import json
import logging
import traceback

from odoo import http
from odoo.http import Response, request

_logger = logging.getLogger(__name__)

# Base64 of a 10 MB file is ~13.3 MB; leave room for the JSON envelope. The
# proxy should enforce a similar client_max_body_size (~14m).
MAX_REQUEST_BODY_BYTES = 15 * 1024 * 1024


class OficialidadDocumentsWebhook(http.Controller):
    @staticmethod
    def _json_response(payload, status=200):
        return Response(
            json.dumps(payload),
            content_type='application/json; charset=utf-8',
            status=status,
        )

    @classmethod
    def _body_too_large_response(cls):
        return cls._json_response({
            'ok': False,
            'error': 'file_too_large',
            'message': 'El cuerpo de la peticion supera el limite permitido.',
        }, status=413)

    @http.route(
        '/irg/oficialidad/webhook/document',
        type='http',
        auth='none',
        methods=['POST'],
        csrf=False,
    )
    def oficialidad_document_webhook(self, **kwargs):
        service = request.env['irg.oficialidad.webhook.service'].sudo()
        # 1. Token first: nothing else is read or parsed for unauthenticated calls.
        auth_error = service.validate_authorization(
            request.httprequest.headers.get('Authorization')
        )
        if auth_error:
            _logger.warning('Oficialidad webhook rejected: %s', auth_error['error'])
            return self._json_response(auth_error, status=401)

        # 2. Bound memory use before reading/parsing the body.
        content_length = request.httprequest.content_length
        if content_length is not None and content_length > MAX_REQUEST_BODY_BYTES:
            return self._body_too_large_response()
        raw_body = request.httprequest.get_data()
        if len(raw_body) > MAX_REQUEST_BODY_BYTES:
            return self._body_too_large_response()

        try:
            payload = json.loads(raw_body.decode('utf-8') or '{}')
        except ValueError:  # includes UnicodeDecodeError and JSONDecodeError
            return self._json_response({
                'ok': False,
                'error': 'invalid_json',
                'message': 'El cuerpo de la peticion debe ser JSON valido.',
            }, status=400)

        try:
            result, status = service.process_payload(payload)
        except Exception as exc:
            # Defense in depth: never let a half-processed request be committed.
            request.env.cr.rollback()
            # Never log the payload (PII/base64), the token or the exception
            # message (it may echo input): only the exception class and the
            # code location.
            _logger.error(
                'Unexpected oficialidad webhook error (%s):\n%s',
                type(exc).__name__,
                ''.join(traceback.format_tb(exc.__traceback__)),
            )
            return self._json_response({
                'ok': False,
                'error': 'server_error',
                'message': 'No se pudo procesar la documentacion de oficialidad.',
            }, status=500)
        return self._json_response(result, status=status)
