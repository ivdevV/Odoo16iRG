# -*- coding: utf-8 -*-
import uuid

from odoo.exceptions import AccessError, MissingError

class OralCaseFixture(object):
    """Datos mínimos de un artículo con caso oral. El entorno de partida es superusuario."""

    def setUp(self):
        super().setUp()
        self.api_key = 'test-irg-oral-key'
        token = uuid.uuid4().hex[:10]
        Users = self.env['res.users'].with_context(no_reset_password=True)
        portal = self.env.ref('base.group_portal')
        faculty = self.env.ref('openeducat_core.group_op_faculty')
        internal = self.env.ref('base.group_user')
        self.student_login = 'oral-student-%s@example.test' % token
        self.other_login = 'oral-other-%s@example.test' % token
        self.teacher_login = 'oral-teacher-%s@example.test' % token
        self.internal_login = 'oral-internal-%s@example.test' % token
        self.student = Users.create({
            'name': 'Alumno caso oral',
            'login': self.student_login,
            'password': self.student_login,
            'groups_id': [(6, 0, [portal.id])],
        })
        self.other_student = Users.create({
            'name': 'Otro alumno caso oral',
            'login': self.other_login,
            'password': self.other_login,
            'groups_id': [(6, 0, [portal.id])],
        })
        self.teacher = Users.create({
            'name': 'Docente caso oral',
            'login': self.teacher_login,
            'password': self.teacher_login,
            'groups_id': [(6, 0, [faculty.id])],
        })
        self.internal_user = Users.create({
            'name': 'Usuario interno caso oral',
            'login': self.internal_login,
            'password': self.internal_login,
            'groups_id': [(6, 0, [internal.id])],
        })
        self.channel = self.env['slide.channel'].create({
            'name': 'Canal caso oral %s' % token,
            'enroll': 'invite',
        })
        self.survey = self.env['survey.survey'].create({
            'title': 'Rúbrica caso oral %s' % token,
        })
        if 'survey_type' in self.survey._fields:
            self.survey.survey_type = 'exam'
        html = '<p id="oral-html">grabacion %s</p>' % token
        slide_vals = {
            'name': 'Caso oral %s' % token,
            'channel_id': self.channel.id,
            'slide_category': 'article',
            'is_published': True,
            'html_content': html,
            'oral_case_enabled': True,
            'oral_case_code': 'DA-ORAL-001',
            'oral_case_survey_id': self.survey.id,
        }
        self.slide = self.env['slide.slide'].create(slide_vals)
        self.html_before = self.slide.html_content
        self.embed_before = (
            self.slide.html_embed_code if 'html_embed_code' in self.slide._fields else None
        )
        self.env['slide.channel.partner'].sudo().create({
            'channel_id': self.channel.id,
            'partner_id': self.student.partner_id.id,
        })
        self._configure_n8n()

    def _configure_n8n(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('irg_oral_case.n8n_submit_url', 'https://n8n.test/webhook/irg-oral-case')
        params.set_param('irg_oral_case.n8n_status_url', 'https://n8n.test/webhook/irg-oral-case-status')
        params.set_param('irg_oral_case.api_key', self.api_key)
        params.set_param('irg_oral_case.max_video_bytes', '52428800')
        params.set_param('irg_oral_case.max_duration_seconds', '600')
        params.set_param('irg_oral_case.retention_enabled', 'False')
        params.set_param('irg_oral_case.retention_days', '0')
        params.set_param('irg_oral_case.store_video_copy', 'False')

    def _form(self, **extra):
        values = {
            'slide_id': str(self.slide.id),
            'consent_date': '2026-10-22',
            'autoevaluacion_json': '{"preparacion": 4}',
            'duracion_seg': '30',
            'partner_id': str(self.other_student.partner_id.id),
            'case_id': 'HACKED',
        }
        values.update(extra)
        return values

    def _video(self, payload=b'\x1a\x45\xdf\xa3webm', filename='caso.webm', content_type='video/webm'):
        stream = _MemoryVideo(payload)
        stream.filename = filename
        stream.content_type = content_type
        return stream

    def _service(self, user):
        return self.env['irg.oral.case.service'].with_user(user)

    def _gradebook_domain(self):
        return [('channel_id', '=', self.channel.id)]

    def _assert_access_blocked(self, func):
        try:
            func()
        except (AccessError, MissingError):
            return
        except Exception as exc:
            self.fail('Se esperaba AccessError o MissingError y llegó %s.' % type(exc).__name__)
        else:
            self.fail('Se esperaba AccessError o MissingError.')


class _MemoryVideo(object):
    def __init__(self, payload):
        self._payload = payload
        self._done = False
        self.filename = 'caso.webm'
        self.content_type = 'video/webm'

    def read(self, size=-1):
        if self._done:
            return b''
        self._done = True
        if size is None or size < 0 or size >= len(self._payload):
            return self._payload
        chunk = self._payload[:size]
        self._payload = self._payload[size:]
        self._done = not self._payload
        return chunk
