# -*- coding: utf-8 -*-
import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrgOralCaseController(http.Controller):

    @http.route(
        '/irg/oral_case/bootstrap',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=True,
        website=True,
        sitemap=False,
    )
    def bootstrap(self, slide_id=None, **kwargs):
        partner = request.env.user.partner_id
        result = request.env['irg.oral.case.service'].bootstrap_meta(partner, slide_id)
        if result['http_status'] == 200:
            # El token es el de la sesión, para el fetch del HTML del slide.
            # La clave de n8n no se añade.
            result['payload']['csrf_token'] = request.csrf_token()
        return _json(result)

    @http.route(
        '/irg/oral_case/submit',
        type='http',
        auth='user',
        methods=['POST'],
        csrf=True,
        website=True,
        sitemap=False,
    )
    def submit(self, **kwargs):
        partner = request.env.user.partner_id
        video = request.httprequest.files.get('video')
        try:
            result = request.env['irg.oral.case.service'].submit_recording(
                partner, request.params, video,
            )
        except Exception:
            _logger.error('irg_oral_case submit failed')
            result = {
                'http_status': 500,
                'payload': {'ok': False, 'error': 'server_error'},
            }
        return _json(result)

    @http.route(
        '/irg/oral_case/status',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=True,
        website=True,
        sitemap=False,
    )
    def status(self, job_id=None, **kwargs):
        partner = request.env.user.partner_id
        try:
            result = request.env['irg.oral.case.service'].fetch_status(partner, job_id)
        except Exception:
            _logger.error('irg_oral_case status failed')
            result = {
                'http_status': 500,
                'payload': {'ok': False, 'error': 'server_error'},
            }
        return _json(result)


def _json(result):
    return request.make_response(
        json.dumps(result['payload'], ensure_ascii=False),
        headers=[('Content-Type', 'application/json')],
        status=result['http_status'],
    )
