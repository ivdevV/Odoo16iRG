# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo import http
from odoo.tests.common import HttpCase, tagged

from .common import OralCaseFixture
from .test_oral_case import FakeResponse, _accepted


@tagged('post_install', '-at_install')
class TestOralCaseHttp(OralCaseFixture, HttpCase):

    def test_anonymous_user_is_sent_to_login(self):
        self.authenticate(None, None)
        response = self.url_open(
            '/irg/oral_case/bootstrap?slide_id=%s' % self.slide.id,
            allow_redirects=False,
        )
        self.assertIn(response.status_code, (302, 303))
        self.assertIn('login', response.headers.get('Location', ''))

    def test_submit_without_csrf_is_rejected(self):
        self.authenticate(self.student_login, self.student_login)
        response = self.url_open(
            '/irg/oral_case/submit',
            data={
                'slide_id': str(self.slide.id),
                'consent_date': '2026-10-22',
                'autoevaluacion_json': '{"preparacion": 4}',
            },
            files={'video': ('caso.webm', b'\x1a\x45\xdf\xa3webm', 'video/webm')},
            allow_redirects=False,
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('csrf', response.text.lower())
        self.assertFalse(self.env['irg.oral.case.job'].search([
            ('partner_id', '=', self.student.partner_id.id),
        ]))

    def test_submit_and_status_do_not_expose_the_key(self):
        self.authenticate(self.student_login, self.student_login)
        csrf = http.Request.csrf_token(self)

        def fake_post(url, data=None, files=None, headers=None, timeout=None, allow_redirects=None):
            self.assertEqual(data['partner_id'], str(self.student.partner_id.id))
            self.assertNotEqual(data['partner_id'], str(self.other_student.partner_id.id))
            self.assertEqual(headers['X-IRG-Key'], self.api_key)
            return _accepted('job-http-1')

        with patch('odoo.addons.irg_oral_case.models.service.requests.post', side_effect=fake_post):
            response = self.url_open(
                '/irg/oral_case/submit',
                data={
                    'csrf_token': csrf,
                    'slide_id': str(self.slide.id),
                    'consent_date': '2026-10-22T10:00:00',
                    'autoevaluacion_json': '{"preparacion": 4}',
                    'duracion_seg': '30',
                    'partner_id': str(self.other_student.partner_id.id),
                    'case_id': 'HACKED',
                },
                files={'video': ('caso.webm', b'\x1a\x45\xdf\xa3webm', 'video/webm')},
            )
        self.assertEqual(response.status_code, 202)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['job_id'], 'job-http-1')
        self.assertTrue(payload['status_url'].startswith('/irg/oral_case/status?job_id='))
        self.assertNotIn(self.api_key, response.text)
        self.assertNotIn('n8n.test', response.text)
        job = self.env['irg.oral.case.job'].search([('n8n_job_id', '=', 'job-http-1')])
        self.assertEqual(job.partner_id, self.student.partner_id)
        self.assertEqual(job.case_code, 'DA-ORAL-001')

        bootstrap = self.url_open('/irg/oral_case/bootstrap?slide_id=%s' % self.slide.id)
        self.assertEqual(bootstrap.status_code, 200)
        boot = bootstrap.json()
        self.assertEqual(boot['case_id'], 'DA-ORAL-001')
        self.assertTrue(boot['csrf_token'])
        self.assertNotIn(self.api_key, bootstrap.text)
        self.assertNotIn('n8n.test', bootstrap.text)
        self.assertNotIn('X-IRG-Key', bootstrap.text)

        def fake_get(url, params=None, headers=None, timeout=None, allow_redirects=None):
            self.assertEqual(headers['X-IRG-Key'], self.api_key)
            return FakeResponse(200, {
                'job_id': 'job-http-1',
                'status': 'queued',
                'score_ia': 4,
                'duracion_fuera_rango': False,
                'user_input_id': 1,
                'error': None,
                'updated_at': '2026-10-22T10:05:00',
                'api_key': self.api_key,
            })

        with patch('odoo.addons.irg_oral_case.models.service.requests.get', side_effect=fake_get):
            own = self.url_open(payload['status_url'])
        self.assertEqual(own.status_code, 200)
        self.assertEqual(own.json()['user_input_id'], job.user_input_id.id)
        self.assertNotIn(self.api_key, own.text)

        self.authenticate(self.other_login, self.other_login)
        with patch('odoo.addons.irg_oral_case.models.service.requests.get') as mocked:
            foreign = self.url_open(payload['status_url'])
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.json()['error'], 'job_not_found')
        self.assertNotIn(self.api_key, foreign.text)
        mocked.assert_not_called()
        self.assertFalse(self.env['app.gradebook.result'].search([
            ('channel_id', '=', self.channel.id),
        ]))
