# -*- coding: utf-8 -*-
import base64
import json
import logging
import math
import os
import re
from datetime import datetime
from urllib.parse import quote

import requests

from odoo import fields, models
from odoo.exceptions import ValidationError

from .oral_case_segment import clean_https_url

_logger = logging.getLogger(__name__)

HARD_MAX_VIDEO_BYTES = 200 * 1024 * 1024
HARD_MAX_DURATION_SECONDS = 14400
MAX_SELF_ASSESSMENT_CHARS = 20000
MAX_CLIPS_JSON_CHARS = 50000
JOB_ID_RE = re.compile(r'^[A-Za-z0-9_.:-]{1,128}$')
N8N_TIMEOUT = 30
PUBLIC_QUEUED_STATUSES = {'queued', 'processing', 'accepted'}
REMOTE_DONE_STATUSES = {'done', 'completed', 'scored'}
REMOTE_ERROR_STATUSES = {'error', 'failed', 'failure'}
VIDEO_WEBM = 'video/webm'
VIDEO_MP4 = 'video/mp4'
ALLOWED_VIDEO_TYPES = {'', 'application/octet-stream', VIDEO_WEBM, VIDEO_MP4}

PARAM_SUBMIT_URL = 'irg_oral_case.n8n_submit_url'
PARAM_STATUS_URL = 'irg_oral_case.n8n_status_url'
PARAM_API_KEY = 'irg_oral_case.api_key'
ENV_SUBMIT_URL = 'IRG_ORAL_CASE_N8N_SUBMIT_URL'
ENV_STATUS_URL = 'IRG_ORAL_CASE_N8N_STATUS_URL'
ENV_API_KEY = 'IRG_ORAL_CASE_API_KEY'

CONSENT_LEGAL_STATUS = 'pending_legal_review'
CONSENT_TEXT = (
    'Texto provisional, pendiente de validación legal. '
    'Al continuar autorizas que se grabe tu imagen y tu voz para evaluar este caso clínico. '
    'La grabación se envía a un servicio de transcripción y de puntuación. '
    'La nota final la decide el profesor. '
    'Este texto todavía no ha sido revisado por el responsable de protección de datos.'
)


class IrgOralCaseService(models.AbstractModel):
    _name = 'irg.oral.case.service'
    _description = 'Entrega de caso oral hacia n8n'

    def submit_recording(self, partner, form, video=None, clip_files=None):
        """Valida, crea la participación y reenvía la grabación a n8n.

        ``partner`` es el de la sesión, capturado antes de cualquier sudo.
        El formulario no puede cambiarlo.
        """
        form = form or {}
        clip_files = clip_files or {}
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

        raw_json, json_error = self._self_assessment(form)
        if json_error:
            return self._fail(400, json_error)

        if self._already_graded(partner, slide):
            return self._fail(400, 'grade_already_confirmed')

        mode = slide.oral_case_mode or 'single'
        if mode == 'clips':
            return self._submit_clips(
                partner, slide, form, clip_files, video, consent, raw_json,
            )
        if clip_files or _first(form.get('clips_json')) not in (None, False, ''):
            return self._fail(400, 'single_video_expected')
        return self._submit_single(partner, slide, form, video, consent, raw_json)

    def _submit_single(self, partner, slide, form, video, consent, raw_json):
        duration = _parse_duration(_first(form.get('duracion_seg')))
        if duration == 'invalid':
            return self._fail(400, 'invalid_duration')
        max_duration = self._duration_ceiling()
        if duration is not None and duration > max_duration:
            return self._fail(400, 'duration_exceeded')
        raw, filename, mimetype, error = self._read_video(video, 'oral-case.webm')
        if error:
            return self._fail(400, error)

        config = self._n8n_config()
        if not config['submit_url'] or not config['api_key']:
            _logger.error('irg_oral_case submit refused: n8n is not configured')
            return self._fail(503, 'n8n_not_configured')

        user_input = self._get_or_create_user_input(partner, slide)
        job = self._create_job(partner, slide, user_input, consent, duration or 0.0, raw_json)
        self._store_video_copy(
            job, raw, filename, mimetype, 'irg.oral.case.job', job.id, 'video_attachment_id',
        )

        data = self._base_payload(partner, slide, raw_json, consent)
        if duration is not None:
            data['duracion_seg'] = str(duration)
        files = {'video': (filename, raw, mimetype)}
        return self._post_n8n(job, config, data, files)

    def _submit_clips(self, partner, slide, form, clip_files, video, consent, raw_json):
        if video is not None and not clip_files:
            return self._fail(400, 'clips_required')
        segments = slide.oral_case_segment_ids.sorted(key=lambda item: (item.sequence, item.id))
        if not segments:
            return self._fail(400, 'invalid_case_config')
        try:
            for segment in segments:
                clean_https_url(segment.clip_url, required=True)
                if segment.listen_clip_url:
                    clean_https_url(segment.listen_clip_url, required=True)
            if slide.oral_case_listen_clip_url:
                clean_https_url(slide.oral_case_listen_clip_url, required=True)
        except ValidationError:
            return self._fail(400, 'invalid_case_config')

        raw_meta = _first(form.get('clips_json'))
        if raw_meta in (None, False, ''):
            return self._fail(400, 'clips_required')
        if not isinstance(raw_meta, str):
            raw_meta = str(raw_meta)
        if len(raw_meta) > MAX_CLIPS_JSON_CHARS:
            return self._fail(400, 'clips_mismatch')
        try:
            parsed = json.loads(raw_meta)
        except (TypeError, ValueError):
            return self._fail(400, 'clips_mismatch')
        if not isinstance(parsed, list) or len(parsed) != len(segments):
            return self._fail(400, 'clips_mismatch')

        prepared_meta = []
        expected_keys = set()
        for index, segment in enumerate(segments, start=1):
            item = parsed[index - 1]
            if not isinstance(item, dict):
                return self._fail(400, 'clips_mismatch')
            if item.get('index') != index or item.get('segment_id') != segment.id:
                return self._fail(400, 'clips_mismatch')
            duration = _parse_duration(item.get('duration_seconds'))
            if duration in ('invalid', None):
                return self._fail(400, 'invalid_duration')
            if duration > self._segment_limit(segment):
                return self._fail(400, 'duration_exceeded')
            key = 'clip_%d' % index
            expected_keys.add(key)
            prepared_meta.append({
                'index': index,
                'segment': segment,
                'duration': duration,
                'key': key,
            })
        if set(clip_files) - expected_keys:
            return self._fail(400, 'clips_mismatch')

        prepared = []
        total = 0
        for item in prepared_meta:
            raw, filename, mimetype, error = self._read_video(
                clip_files.get(item['key']), 'clip-%d.webm' % item['index'],
            )
            if error:
                return self._fail(400, error)
            total += len(raw)
            if total > HARD_MAX_VIDEO_BYTES:
                return self._fail(400, 'video_too_large')
            prepared.append({
                'index': item['index'],
                'segment': item['segment'],
                'duration': item['duration'],
                'raw': raw,
                'filename': filename,
                'mimetype': mimetype,
            })

        config = self._n8n_config()
        if not config['submit_url'] or not config['api_key']:
            _logger.error('irg_oral_case submit refused: n8n is not configured')
            return self._fail(503, 'n8n_not_configured')

        user_input = self._get_or_create_user_input(partner, slide)
        total_duration = sum(item['duration'] for item in prepared)
        job = self._create_job(partner, slide, user_input, consent, total_duration, raw_json)
        clips_meta = []
        files = {}
        for item in prepared:
            segment = item['segment']
            clip = self.env['irg.oral.case.clip'].sudo().create({
                'job_id': job.id,
                'segment_id': segment.id,
                'segment_index': item['index'],
                'prompt_snapshot': segment.prompt,
                'student_text_snapshot': segment.student_text or segment.prompt,
                'clip_url_snapshot': segment.clip_url,
                'duration_seconds': item['duration'],
            })
            self._store_video_copy(
                job, item['raw'], item['filename'], item['mimetype'],
                'irg.oral.case.clip', clip.id, None, clip=clip,
            )
            clips_meta.append({
                'index': item['index'],
                'segment_id': segment.id,
                'name': segment.name,
                'prompt': segment.prompt,
                'clip_url': segment.clip_url,
                'max_seconds': self._segment_limit(segment),
                'duration_seconds': item['duration'],
            })
            files['clip_%d' % item['index']] = (item['filename'], item['raw'], item['mimetype'])
        data = self._base_payload(partner, slide, raw_json, consent)
        data['mode'] = 'clips'
        data['case_title'] = slide.name or ''
        data['clips_json'] = json.dumps(clips_meta, ensure_ascii=False, separators=(',', ':'))
        data['duracion_seg'] = str(total_duration)
        return self._post_n8n(job, config, data, files)

    def _post_n8n(self, job, config, data, files):
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
        raw_status = body.get('status') if isinstance(body.get('status'), str) and body.get('status') else 'accepted'
        public_status = 'queued' if raw_status in PUBLIC_QUEUED_STATUSES else _clip(raw_status, 64)
        self._dispatch(job, {
            'state': 'accepted',
            'n8n_job_id': job_id,
            'n8n_status': _clip(raw_status, 64),
            'last_error': False,
        })
        return {
            'http_status': 202,
            'payload': {
                'ok': True,
                'job_id': job_id,
                'status': public_status,
                'status_url': '/irg/oral_case/status?job_id=%s' % quote(job_id),
            },
        }

    def fetch_status(self, partner, job_id):
        if not isinstance(job_id, str) or not JOB_ID_RE.match(job_id or ''):
            return self._fail(400, 'invalid_job_id')
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
        payload = self._apply_remote_status(job, remote, config['api_key'])
        return {'http_status': 200, 'payload': payload}

    def _refresh_pending_jobs(self):
        """Consulta n8n para entregas aún aceptadas. No toca la nota oficial."""
        job_model = self.env['irg.oral.case.job']
        if job_model._irg_module_operation_in_progress():
            return False
        config = self._n8n_config()
        if not config['status_url'] or not config['api_key']:
            _logger.error('irg_oral_case status refresh skipped: n8n is not configured')
            return False
        from datetime import timedelta
        horizon = fields.Datetime.now() - timedelta(days=7)
        jobs = job_model.sudo().search([
            ('state', '=', 'accepted'),
            ('n8n_job_id', '!=', False),
            ('create_date', '>=', horizon),
        ], limit=20, order='write_date asc, id asc')
        for job in jobs:
            self._refresh_job(job, config)
        return True

    def _refresh_job(self, job, config):
        try:
            response = requests.get(
                config['status_url'],
                params={'job_id': job.n8n_job_id},
                headers={'X-IRG-Key': config['api_key']},
                timeout=N8N_TIMEOUT,
                allow_redirects=False,
            )
        except requests.RequestException:
            _logger.error('irg_oral_case status refresh transport error for job %s', job.id)
            return
        if response.status_code != 200:
            _logger.error(
                'irg_oral_case status refresh unexpected status %s', response.status_code,
            )
            return
        self._apply_remote_status(job, _response_json(response), config['api_key'])

    def _apply_remote_status(self, job, remote, secret):
        payload = _status_payload(remote, job, secret)
        vals = _remote_job_vals(
            payload.get('status'),
            remote.get('error') if isinstance(remote.get('error'), str) else None,
            secret,
        )
        if vals:
            self._dispatch(job, vals)
        self._persist_suggestion(job, remote)
        return payload

    def bootstrap_meta(self, partner, slide_id):
        slide, error = self._load_accessible_slide(partner, slide_id)
        if error:
            return error
        if not slide.oral_case_enabled or not slide.oral_case_code or not slide.oral_case_survey_id:
            return self._fail(400, 'not_oral_case')
        mode = slide.oral_case_mode or 'single'
        segments_payload = []
        if mode == 'clips':
            segments = slide.oral_case_segment_ids.sorted(key=lambda item: (item.sequence, item.id))
            if not segments:
                return self._fail(400, 'invalid_case_config')
            try:
                listen_case = clean_https_url(slide.oral_case_listen_clip_url) if slide.oral_case_listen_clip_url else ''
            except ValidationError:
                return self._fail(400, 'invalid_case_config')
            for index, segment in enumerate(segments, start=1):
                try:
                    clip_url = clean_https_url(segment.clip_url, required=True)
                    listen = clean_https_url(segment.listen_clip_url) if segment.listen_clip_url else listen_case
                except ValidationError:
                    return self._fail(400, 'invalid_case_config')
                segments_payload.append({
                    'id': segment.id,
                    'index': index,
                    'sequence': segment.sequence,
                    'name': segment.name,
                    'clip_url': clip_url,
                    'student_text': segment.student_text or segment.prompt or '',
                    'student_quote': segment.student_quote or '',
                    'transcript': segment.transcript or '',
                    'max_seconds': self._segment_limit(segment),
                    'allow_retry': bool(segment.allow_retry),
                    'listen_clip_url': listen or '',
                })
        else:
            listen_case = ''
        return {
            'http_status': 200,
            'payload': {
                'ok': True,
                'slide_id': slide.id,
                'case_id': slide.oral_case_code,
                'case_title': slide.name or '',
                'keep_video': self._keep_video(slide),
                'mode': mode,
                'consent_text': CONSENT_TEXT,
                'consent_legal_status': CONSENT_LEGAL_STATUS,
                'listen_clip_url': listen_case if mode != 'clips' else '',
                'max_video_bytes': self._int_param(
                    'irg_oral_case.max_video_bytes', 52428800, HARD_MAX_VIDEO_BYTES,
                ),
                'max_duration_seconds': self._duration_ceiling(),
                'submit_url': '/irg/oral_case/submit',
                'status_url': '/irg/oral_case/status',
                'segments': segments_payload,
            },
        }

    def _persist_suggestion(self, job, remote):
        """Guarda solo la sugerencia. No toca la nota final ni los enlaces."""
        vals = {}
        score = _optional_score(remote.get('score_ia'))
        if score is not None:
            vals['score_ia'] = score
        summary = remote.get('resumen_ia')
        if isinstance(summary, str):
            vals['resumen_ia'] = summary[:8000]
        if vals and job.user_input_id:
            job.user_input_id.sudo().write(vals)
        tramos = remote.get('tramos')
        if not isinstance(tramos, list):
            return
        for item in tramos:
            if not isinstance(item, dict) or not isinstance(item.get('index'), int):
                continue
            clip = job.clip_ids.filtered(lambda record: record.segment_index == item['index'])[:1]
            if not clip:
                continue
            clip_vals = {}
            clip_score = _optional_score(item.get('score_ia'))
            if clip_score is not None:
                clip_vals['score_ia'] = clip_score
            clip_summary = item.get('resumen_ia')
            if isinstance(clip_summary, str):
                clip_vals['resumen_ia'] = clip_summary[:8000]
            if clip_vals:
                clip.sudo().write(clip_vals)

    def _load_accessible_slide(self, partner, slide_id):
        slide_int = _as_int(slide_id)
        if not slide_int:
            return None, self._fail(400, 'missing_slide')
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
        return bool(self.env['slide.channel.partner'].sudo().search_count([
            ('channel_id', '=', slide.channel_id.id),
            ('partner_id', '=', partner.id),
        ]))

    def _get_or_create_user_input(self, partner, slide):
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

    def _create_job(self, partner, slide, user_input, consent, duration, raw_json):
        return self.env['irg.oral.case.job'].sudo().with_context(
            mail_create_nosubscribe=True,
            mail_create_nolog=True,
            tracking_disable=True,
        ).create({
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

    def _store_video_copy(self, job, raw, filename, mimetype, res_model, res_id, job_field, clip=None):
        if not self._keep_video(job.slide_id):
            return
        attachment = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'datas': base64.b64encode(raw),
            'res_model': res_model,
            'res_id': res_id,
            'type': 'binary',
            'mimetype': mimetype,
            'public': False,
        })
        if clip is not None:
            clip.sudo().write({'video_attachment_id': attachment.id})
        elif job_field:
            self._dispatch(job, {job_field: attachment.id})
        if not job.video_stored_at:
            self._dispatch(job, {'video_stored_at': fields.Datetime.now()})

    def _keep_video(self, slide):
        if slide.oral_case_keep_video:
            return True
        return self._bool_param('irg_oral_case.store_video_copy')

    def _already_graded(self, partner, slide):
        if self.env['irg.oral.case.job'].sudo().search_count([
            ('partner_id', '=', partner.id),
            ('slide_id', '=', slide.id),
            ('official_confirmed_at', '!=', False),
        ]):
            return True
        inputs = self.env['survey.user_input'].sudo().search([
            ('partner_id', '=', partner.id),
            ('slide_id', '=', slide.id),
            ('survey_id', '=', slide.oral_case_survey_id.id),
            ('test_entry', '=', False),
        ])
        if not inputs:
            return False
        return bool(self.env['app.gradebook.result'].sudo().search_count([
            ('survey_user_input_id', 'in', inputs.ids),
        ]))

    def _base_payload(self, partner, slide, raw_json, consent):
        return {
            'case_id': slide.oral_case_code,
            'slide_id': str(slide.id),
            'partner_id': str(partner.id),
            'autoevaluacion_json': raw_json,
            'consent_date': consent.strftime('%Y-%m-%dT%H:%M:%S'),
        }

    def _self_assessment(self, form):
        raw_json = _first(form.get('autoevaluacion_json'))
        if raw_json in (None, False, ''):
            return None, 'missing_self_assessment'
        if not isinstance(raw_json, str):
            raw_json = str(raw_json)
        parsed_json, json_error = _parse_self_assessment(raw_json)
        if json_error:
            return None, json_error
        return json.dumps(parsed_json, ensure_ascii=False, separators=(',', ':')), None

    def _read_video(self, video, fallback='oral-case.webm'):
        if video is None:
            return b'', fallback, VIDEO_WEBM, 'missing_video'
        content_type = _video_content_type(video)
        if content_type not in ALLOWED_VIDEO_TYPES:
            return b'', fallback, VIDEO_WEBM, 'invalid_video_type'
        filename = _safe_filename(getattr(video, 'filename', '') or fallback)
        expected = _expected_container(content_type, filename)
        if not expected:
            return b'', fallback, VIDEO_WEBM, 'invalid_video_type'
        max_bytes = self._int_param(
            'irg_oral_case.max_video_bytes', 52428800, HARD_MAX_VIDEO_BYTES,
        )
        raw, too_big = _read_limited(video, max_bytes)
        if too_big:
            return b'', fallback, VIDEO_WEBM, 'video_too_large'
        if not raw:
            return b'', fallback, VIDEO_WEBM, 'empty_video'
        sniffed = _sniff_container(raw)
        if sniffed != expected:
            return b'', fallback, VIDEO_WEBM, 'invalid_video_type'
        mimetype = VIDEO_MP4 if sniffed == 'mp4' else VIDEO_WEBM
        return raw, _server_filename(fallback, sniffed), mimetype, None

    def _dispatch(self, job, vals):
        job.sudo().write(vals)

    def _n8n_config(self):
        params = self.env['ir.config_parameter'].sudo()
        return {
            'submit_url': _setting(params, PARAM_SUBMIT_URL, ENV_SUBMIT_URL),
            'status_url': _setting(params, PARAM_STATUS_URL, ENV_STATUS_URL),
            'api_key': _setting(params, PARAM_API_KEY, ENV_API_KEY),
        }

    def _duration_ceiling(self):
        return self._int_param(
            'irg_oral_case.max_duration_seconds', 600, HARD_MAX_DURATION_SECONDS,
        )

    def _segment_limit(self, segment):
        return min(int(segment.max_seconds or 0), self._duration_ceiling(), HARD_MAX_DURATION_SECONDS)

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
    if number < 0 or number != number or math.isinf(number):
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


def _remote_job_vals(remote_status, remote_error, secret):
    if not isinstance(remote_status, str) or not remote_status:
        return {}
    vals = {'n8n_status': _clip(remote_status, 64)}
    if remote_status in REMOTE_DONE_STATUSES:
        vals['state'] = 'done'
        vals['last_error'] = False
    elif remote_status in REMOTE_ERROR_STATUSES:
        vals['state'] = 'error'
        text = remote_error if isinstance(remote_error, str) and remote_error else remote_status
        vals['last_error'] = _clip(_redact(text, secret))
    elif remote_status in PUBLIC_QUEUED_STATUSES:
        vals['state'] = 'accepted'
    return vals


def _expected_container(content_type, filename):
    name = (filename or '').lower()
    if content_type == VIDEO_WEBM:
        return 'webm' if name.endswith('.webm') else None
    if content_type == VIDEO_MP4:
        return 'mp4' if name.endswith('.mp4') else None
    if content_type in ('', 'application/octet-stream'):
        if name.endswith('.webm'):
            return 'webm'
        if name.endswith('.mp4'):
            return 'mp4'
    return None


def _sniff_container(raw):
    if raw.startswith(b'\x1a\x45\xdf\xa3'):
        return 'webm'
    if len(raw) >= 8 and raw[4:8] == b'ftyp':
        return 'mp4'
    return None


def _server_filename(fallback, container):
    base = os.path.splitext(_safe_filename(fallback))[0]
    if not base or base in ('.', '..'):
        base = 'oral-case'
    ext = 'mp4' if container == 'mp4' else 'webm'
    return '%s.%s' % (base, ext)


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


def _optional_score(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if not math.isfinite(value) or value < 0 or value > 10:
        return None
    return value


def _status_payload(remote, job, secret):
    status = remote.get('status') if isinstance(remote.get('status'), str) else None
    score = _optional_score(remote.get('score_ia'))
    duration_flag = remote.get('duracion_fuera_rango')
    if not isinstance(duration_flag, bool):
        duration_flag = None
    error = remote.get('error')
    if not isinstance(error, str):
        error = None
    updated = remote.get('updated_at')
    if not isinstance(updated, str):
        updated = None
    summary = remote.get('resumen_ia') if isinstance(remote.get('resumen_ia'), str) else None
    payload = {
        'job_id': job.n8n_job_id,
        'status': status,
        'score_ia': score,
        'resumen_ia': _clip(_redact(summary, secret), 8000) if summary else None,
        'duracion_fuera_rango': duration_flag,
        'user_input_id': job.user_input_id.id,
        'error': _clip(_redact(error, secret)) if error else None,
        'updated_at': _clip(_redact(updated, secret), 64) if updated else None,
    }
    tramos = []
    raw_tramos = remote.get('tramos')
    if isinstance(raw_tramos, list):
        for item in raw_tramos:
            if not isinstance(item, dict) or not isinstance(item.get('index'), int):
                continue
            item_summary = item.get('resumen_ia') if isinstance(item.get('resumen_ia'), str) else None
            tramos.append({
                'index': item['index'],
                'score_ia': _optional_score(item.get('score_ia')),
                'resumen_ia': _clip(_redact(item_summary, secret), 8000) if item_summary else None,
            })
    if tramos:
        payload['tramos'] = tramos
    return payload


def _redact(value, secret):
    if not value or not secret:
        return value
    return str(value).replace(secret, '***')


def _clip(value, limit=500):
    if not value:
        return value
    return str(value)[:limit]
