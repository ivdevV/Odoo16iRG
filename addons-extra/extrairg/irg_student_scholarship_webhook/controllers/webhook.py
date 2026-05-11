# -*- coding: utf-8 -*-

import json
import logging

from odoo import http
from odoo.http import Response, request


_logger = logging.getLogger(__name__)


class ScholarshipDocumentsWebhook(http.Controller):
    @staticmethod
    def _json_response(payload, status=200):
        return Response(
            json.dumps(payload),
            content_type='application/json; charset=utf-8',
            status=status,
        )

    @http.route(
        '/irg/scholarship/webhook/document',
        type='http',
        auth='none',
        methods=['POST'],
        csrf=False,
    )
    def scholarship_document_webhook(self, **kwargs):
        service = request.env['irg.scholarship.webhook.service'].sudo()
        auth_error = service.validate_authorization(
            request.httprequest.headers.get('Authorization')
        )
        if auth_error:
            return self._json_response(auth_error, status=401)

        try:
            payload = json.loads(request.httprequest.get_data(as_text=True) or '{}')
        except ValueError:
            return self._json_response({
                'ok': False,
                'error': 'invalid_json',
                'message': 'El cuerpo de la peticion debe ser JSON valido.',
            }, status=400)

        try:
            result, status = service.process_payload(payload)
        except Exception:
            _logger.exception('Unexpected scholarship webhook error')
            return self._json_response({
                'ok': False,
                'error': 'server_error',
                'message': 'No se pudo procesar la documentacion de beca.',
            }, status=500)
        return self._json_response(result, status=status)
