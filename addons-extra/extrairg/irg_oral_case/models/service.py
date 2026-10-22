# -*- coding: utf-8 -*-
import base64
import json
import logging
import os
import re
from datetime import datetime
from urllib.parse import quote

import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)

HARD_MAX_VIDEO_BYTES = 200 * 1024 * 1024
HARD_MAX_DURATION_SECONDS = 14400
MAX_SELF_ASSESSMENT_CHARS = 20000
JOB_ID_RE = re.compile(r'^[A-Za-z0-9_.:-]{1,128}$')
N8N_TIMEOUT = 30

PARAM_SUBMIT_URL = 'irg_oral_case.n8n_submit_url'
PARAM_STATUS_URL = 'irg_oral_case.n8n_status_url'
PARAM_API_KEY = 'irg_oral_case.api_key'
ENV_SUBMIT_URL = 'IRG_ORAL_CASE_N8N_SUBMIT_URL'
ENV_STATUS_URL = 'IRG_ORAL_CASE_N8N_STATUS_URL'
ENV_API_KEY = 'IRG_ORAL_CASE_API_KEY'


class IrgOralCaseService(models.AbstractModel):
    _name = 'irg.oral.case.service'
    _description = 'Entrega de caso oral hacia n8n'

    def submit_recording(self, partner, form, video):
        """Valida, crea la participación y reenvía el vídeo a n8n.

        ``partner`` es el de la sesión. El formulario no puede cambiarlo.
        """
        form = form or {}
        slide, error = self._load_accessible_slide(partner, _first(form.get('slide_id')))
        if error:
            return error
        if not slide.oral_case_enabled or not slide.oral_case_code or not slide.oral_case_survey_id:
            return self._fail(400, 'not_oral_case')

        consent = _parse_consent(_first(form.get('consent_date')))
        if _first(form.get('consent_date')) in (None, False, ''):
            return self._fail(400, 'missing_consent')
        if consent is None:
            return self._fail(400, 'invalid_consent')

        raw_json = _first(form.get('autoevaluacion_json'))
        if raw_json in (None, False, ''):
            return self._fail(400, 'missing_self_assessment')
        if not isinstance(raw_json, str):
            raw_json = str(raw_json)
        parsed_json, json_error = _parse_self_assessment(raw_json)
        if json_error:
            return self._fail(400, json_error)
        raw_json = json.dumps(parsed_json, ensure_ascii=False, separators=(',', ':'))

        duration = _parse_duration(_first(form.get('duracion_seg')))
        if duration == 'invalid':
            return self._fail(400, 'invalid_duration')
        max_duration = self._int_param(
            'irg_oral_case.max_duration_seconds', 600, HARD_MAX_DURATION_SECONDS,
        )
        if duration is not None and duration > max_duration:
            return self._fail(400, 'duration_exceeded')

        if video is None:
            return self._fail(400, 'missing_video')
        content_type = _video_content_type(video)
        if content_type and content_type not in ('application/octet-stream', 'video/webm'):
            return self._fail(400, 'invalid_video_type')
        filename = _safe_filename(getattr(video, 'filename', '') or 'oral-case.webm')
        if content_type != 'video/webm' and not filename.endswith('.webm'):
            return self._fail(400, 'invalid_video_type')
        max_bytes = self._int_param(
            'irg_oral_case.max_video_bytes', 52428800, HARD_MAX_VIDEO_BYTES,
        )
        raw, too_big = _read_limited(video, max_bytes)
        if too_big:
            return self._fail(400, 'video_too_large')
        if not raw:
            return self._fail(400, 'empty_video')

        config = self._n8n_config()
        if not config['submit_url'] or not config['api_key']:
            _logger.error('irg_oral_case submit refused: n8n is not configured')
            return self._fail(503, 'n8n_not_configured')

        user_input = self._get_or_create_user_input(partner, slide)
        job = self.env['irg.oral.case.job'].create({
            'partner_id': partner.id,
            'slide_id': slide.id,
            'survey_id': slide.oral_case_survey_id.id,
            'user_input_id': user_input.id,
            'case_code': slide.oral_case_code,
            'consent_date': consent,
            'duration_seconds': duration or 0.0,
            'autoevaluacion_json': raw_json,
            'state': 'draft',
        })
        self._store_video_copy(job, raw, filename)

        data = {
            'case_id': slide.oral_case_code,
            'slide_id': str(slide.id),
            'partner_id': str(partner.id),
            'autoevaluacion_json': raw_json,
            'consent_date': consent.strftime('%Y-%m-%dT%H:%M:%S'),
        }
        if duration is not None:
            data['duracion_seg'] = str(duration)
        files = {
            'video': (filename, raw, 'video/webm'),
        }
        try:
            response = requests.post(
                config['submit_url'],
                data=data,
                files=files,
                headers={'X-IRG-Key': config['api_key']},
                timeout=N8N_TIMEOUT,
                allow_redirects=False,
            )
        except requests.RequestException:
            _logger.error('irg_oral_case submit transport error')
            self._dispatch(job, {'state': 'error', 'last_error': 'n8n_unavailable'})
            return self._fail(502, 'n8n_unavailable')

        body = _response_json(response)
        secret = config['api_key']
        if response.status_code == 400 or (response.status_code == 202 and not body.get('ok')):
            errors = _public_errors(body.get('errors'), secret)
            self._dispatch(job, {
                'state': 'rejected',
                'last_error': _clip(_redact(json.dumps(errors, ensure_ascii=False), secret)),
            })
            return self._fail(400, 'n8n_rejected', errors)
        if response.status_code != 202 or not body.get('ok'):
            _logger.error('irg_oral_case submit unexpected status %s', response.status_code)
            self._dispatch(job, {'state': 'error', 'last_error': 'n8n_unavailable'})
            return self._fail(502, 'n8n_unavailable')
        job_id = body.get('job_id')
        if not isinstance(job_id, str) or not JOB_ID_RE.match(job_id):
            self._dispatch(job, {'state': 'error', 'last_error': 'n8n_unavailable'})
            return self._fail(502, 'n8n_unavailable')
        status = body.get('status') if isinstance(body.get('status'), str) else 'accepted'
        self._dispatch(job, {
            'state': 'accepted',
            'n8n_job_id': job_id,
            'n8n_status': _clip(status, 64),
            'last_error': False,
        })
        return {
            'http_status': 202,
            'payload': {
                'ok': True,
                'job_id': job_id,
                'status': status,
                'status_url': '/irg/oral_case/status?job_id=%s' % quote(job_id),
            },
        }

    def fetch_status(self, partner, job_id):
        if not isinstance(job_id, str) or not JOB_ID_RE.match(job_id or ''):
            return self._fail(400, 'invalid_job_id')
        # sudo con el partner de la sesión dentro del dominio: un alumno no
        # puede leer el job de otro aunque falle una regla de registro.
        job = self.env['irg.oral.case.job'].sudo().search([
            ('n8n_job_id', '=', job_id),
            ('partner_id', '=', partner.id),
        ], limit=1)
        if not job:
            return self._fail(404, 'job_not_found')
        config = self._n8n_config()
        if not config['status_url'] or not config['api_key']:
            _logger.error('irg_oral_case status refused: n8n is not configured')
            return self._fail(503, 'n8n_not_configured')
        try:
            response = requests.get(
                config['status_url'],
                params={'job_id': job_id},
                headers={'X-IRG-Key': config['api_key']},
                timeout=N8N_TIMEOUT,
                allow_redirects=False,
            )
        except requests.RequestException:
            _logger.error('irg_oral_case status transport error')
            return self._fail(502, 'n8n_unavailable')
        if response.status_code != 200:
            _logger.error('irg_oral_case status unexpected status %s', response.status_code)
            return self._fail(502, 'n8n_unavailable')
        remote = _response_json(response)
        payload = _status_payload(remote, job, config['api_key'])
        remote_status = payload.get('status')
        if isinstance(remote_status, str):
            self._dispatch(job, {'n8n_status': _clip(remote_status, 64)})
        return {'http_status': 200, 'payload': payload}

    def bootstrap_meta(self, partner, slide_id):
        slide, error = self._load_accessible_slide(partner, slide_id)
        if error:
            return error
        if not slide.oral_case_enabled or not slide.oral_case_code or not slide.oral_case_survey_id:
            return self._fail(400, 'not_oral_case')
        return {
            'http_status': 200,
            'payload': {
                'ok': True,
                'slide_id': slide.id,
                'case_id': slide.oral_case_code,
                'max_video_bytes': self._int_param(
                    'irg_oral_case.max_video_bytes', 52428800, HARD_MAX_VIDEO_BYTES,
                ),
                'max_duration_seconds': self._int_param(
                    'irg_oral_case.max_duration_seconds', 600, HARD_MAX_DURATION_SECONDS,
                ),
                'submit_url': '/irg/oral_case/submit',
                'status_url': '/irg/oral_case/status',
            },
        }

    def _load_accessible_slide(self, partner, slide_id):
        slide_int = _as_int(slide_id)
        if not slide_int:
            return None, self._fail(400, 'missing_slide')
        # sudo solo para distinguir "no existe" de "no es tuyo". No se devuelve
        # el HTML ni ningún campo si el acceso falla.
        slide = self.env['slide.slide'].sudo().browse(slide_int).exists()
        if not slide:
            return None, self._fail(404, 'slide_not_found')
        if not self._partner_can_access_slide(partner, slide):
            return None, self._fail(403, 'slide_forbidden')
        return slide, None

    def _partner_can_access_slide(self, partner, slide):
        if not partner or not slide or slide.is_category:
            return False
        is_faculty = self.env.user.has_group('openeducat_core.group_op_faculty')
        if not slide.is_published and not is_faculty:
            return False
        if is_faculty:
            return True
        # sudo: algunas reglas ocultan slide.channel.partner al propio alumno.
        # El dominio sigue siendo el partner de la sesión.
        return bool(self.env['slide.channel.partner'].sudo().search_count([
            ('channel_id', '=', slide.channel_id.id),
            ('partner_id', '=', partner.id),
        ]))

    def _get_or_create_user_input(self, partner, slide):
        # sudo: el portal no tiene permiso de alta sobre survey.user_input.
        # Solo se crea o reutiliza la participación de este partner y este slide,
        # en curso, para que isep_gradebook no llame a send_result (exige done).
        user_input_model = self.env['survey.user_input'].sudo()
        existing = user_input_model.search([
            ('survey_id', '=', slide.oral_case_survey_id.id),
            ('partner_id', '=', partner.id),
            ('slide_id', '=', slide.id),
            ('test_entry', '=', False),
        ], order='id desc', limit=1)
        if existing:
            return existing
        return user_input_model.create({
            'survey_id': slide.oral_case_survey_id.id,
            'partner_id': partner.id,
            'slide_id': slide.id,
            'state': 'in_progress',
            'test_entry': False,
        })

    def _store_video_copy(self, job, raw, filename):
        if not self._bool_param('irg_oral_case.store_video_copy'):
            return
        # sudo: el adjunto queda privado y ligado al job. El portal no puede
        # crear ir.attachment sobre ese modelo.
        attachment = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'datas': base64.b64encode(raw),
            'res_model': 'irg.oral.case.job',
            'res_id': job.id,
            'type': 'binary',
            'mimetype': 'video/webm',
            'public': False,
        })
        self._dispatch(job, {
            'video_attachment_id': attachment.id,
            'video_stored_at': fields.Datetime.now(),
        })

    def _dispatch(self, job, vals):
        job.with_context(irg_oral_case_dispatch=True).sudo().write(vals)

    def _n8n_config(self):
        # sudo: ir.config_parameter no es legible por el portal. El valor no
        # sale de este método hacia la respuesta HTTP.
        params = self.env['ir.config_parameter'].sudo()
        return {
            'submit_url': _setting(params, PARAM_SUBMIT_URL, ENV_SUBMIT_URL),
            'status_url': _setting(params, PARAM_STATUS_URL, ENV_STATUS_URL),
            'api_key': _setting(params, PARAM_API_KEY, ENV_API_KEY),
        }

    def _int_param(self, key, default, ceiling):
        raw = self.env['ir.config_parameter'].sudo().get_param(key, default)
        try:
            value = int(raw)
        except (TypeError, ValueError):
            value = default
        if value < 0:
            value = 0
        return min(value, ceiling)

    def _bool_param(self, key):
        raw = self.env['ir.config_parameter'].sudo().get_param(key, 'False')
        return str(raw or '').strip().lower() in ('1', 'true', 'yes', 'on')

    def _fail(self, status, error, errors=None):
        payload = {'ok': False, 'error': error}
        if errors is not None:
            payload['errors'] = errors
        return {'http_status': status, 'payload': payload}


def _setting(params, key, env_name):
    env_value = os.environ.get(env_name)
    if isinstance(env_value, str) and env_value.strip():
        return env_value.strip()
    value = params.get_param(key) or ''
    return value.strip() if isinstance(value, str) else ''


def _first(value):
    if isinstance(value, (list, tuple)):
        return value[0] if value else ''
    return value


def _as_int(value):
    value = _first(value)
    if isinstance(value, bool) or value in (None, ''):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_consent(value):
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith('Z'):
        text = text[:-1]
    if '+' in text[10:]:
        text = text.split('+', 1)[0]
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f'):
        try:
            parsed = datetime.strptime(text, fmt)
            if fmt == '%Y-%m-%d':
                return parsed.replace(hour=0, minute=0, second=0)
            return parsed
        except ValueError:
            continue
    return None


def _parse_duration(value):
    if value in (None, False, ''):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 'invalid'
    if number < 0 or number != number:
        return 'invalid'
    return number


def _parse_self_assessment(raw):
    if len(raw) > MAX_SELF_ASSESSMENT_CHARS:
        return None, 'invalid_self_assessment'
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return None, 'invalid_self_assessment'
    if not isinstance(parsed, (dict, list)):
        return None, 'invalid_self_assessment'
    return parsed, None


def _video_content_type(video):
    raw = getattr(video, 'content_type', None) or getattr(video, 'mimetype', None) or ''
    return str(raw).split(';', 1)[0].strip().lower()


def _safe_filename(name):
    base = os.path.basename(str(name or '')).replace('\x00', '').strip()
    if not base or base in ('.', '..'):
        base = 'oral-case.webm'
    return base[-128:]


def _read_limited(video, limit):
    chunks = []
    total = 0
    while True:
        chunk = video.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            return b'', True
        chunks.append(chunk)
    return b''.join(chunks), False


def _response_json(response):
    try:
        payload = response.json()
    except ValueError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _public_errors(errors, secret):
    if isinstance(errors, str):
        items = [errors]
    elif isinstance(errors, list):
        items = [item for item in errors if isinstance(item, str)]
    else:
        items = []
    return [_clip(_redact(item, secret)) for item in items[:20]]


def _status_payload(remote, job, secret):
    status = remote.get('status') if isinstance(remote.get('status'), str) else None
    score = remote.get('score_ia')
    if isinstance(score, bool) or not isinstance(score, (int, float)):
        score = None
    duration_flag = remote.get('duracion_fuera_rango')
    if not isinstance(duration_flag, bool):
        duration_flag = None
    error = remote.get('error')
    if not isinstance(error, str):
        error = None
    updated = remote.get('updated_at')
    if not isinstance(updated, str):
        updated = None
    payload = {
        'job_id': job.n8n_job_id,
        'status': status,
        'score_ia': score,
        'duracion_fuera_rango': duration_flag,
        'user_input_id': job.user_input_id.id,
        'error': _clip(_redact(error, secret)) if error else None,
        'updated_at': _clip(_redact(updated, secret), 64) if updated else None,
    }
    return payload


def _redact(value, secret):
    if not value or not secret:
        return value
    return str(value).replace(secret, '***')


def _clip(value, limit=500):
    if not value:
        return value
    return str(value)[:limit]
