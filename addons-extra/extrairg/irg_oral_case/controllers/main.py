# -*- coding: utf-8 -*-
import base64
import json
import logging

from odoo import http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request

from odoo.addons.irg_oral_case.models.oral_case_job import attachment_is_case_video

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
        files = request.httprequest.files
        video = files.get('video')
        clip_files = {}
        for key in files:
            suffix = key[5:] if key.startswith('clip_') else ''
            if suffix.isdigit():
                clip_files[key] = files.get(key)
        try:
            result = request.env['irg.oral.case.service'].submit_recording(
                partner, request.params, video, clip_files,
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

    @http.route(
        '/irg/oral_case/media/job/<int:job_id>',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
        website=True,
        sitemap=False,
    )
    def media_job(self, job_id, **kwargs):
        job = _visible_job(job_id)
        if not job:
            return _not_found()
        # El id sale de la entrega ya autorizada. El portal no tiene por qué
        # poder leer ir.attachment; el vínculo se comprueba en sudo.
        attachment = job.sudo().video_attachment_id
        return _stream_case_video(attachment, 'irg.oral.case.job', job.id)

    @http.route(
        '/irg/oral_case/media/job/<int:job_id>/clip/<int:clip_id>',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
        website=True,
        sitemap=False,
    )
    def media_clip(self, job_id, clip_id, **kwargs):
        job = _visible_job(job_id)
        if not job:
            return _not_found()
        clip = request.env['irg.oral.case.clip'].sudo().browse(clip_id)
        if not clip.exists() or clip.job_id != job:
            return _not_found()
        return _stream_case_video(clip.video_attachment_id, 'irg.oral.case.clip', clip.id)


def _visible_job(job_id):
    job = request.env['irg.oral.case.job'].browse(job_id)
    try:
        job.check_access_rights('read')
        job.check_access_rule('read')
        if not job.exists():
            return None
    except (AccessError, MissingError):
        return None
    return job


def _stream_case_video(attachment, res_model, res_id):
    if not attachment_is_case_video(attachment, res_model, res_id):
        return _not_found()
    raw = base64.b64decode(attachment.sudo().datas or b'')
    if not raw:
        return _not_found()
    return request.make_response(raw, [
        ('Content-Type', 'video/webm'),
        ('X-Content-Type-Options', 'nosniff'),
        ('Content-Disposition', 'inline'),
        ('Cache-Control', 'private, no-store'),
        ('Content-Length', str(len(raw))),
    ])


def _not_found():
    return request.make_response(
        json.dumps({'ok': False, 'error': 'not_found'}),
        headers=[('Content-Type', 'application/json')],
        status=404,
    )


def _json(result):
    return request.make_response(
        json.dumps(result['payload'], ensure_ascii=False),
        headers=[('Content-Type', 'application/json')],
        status=result['http_status'],
    )
