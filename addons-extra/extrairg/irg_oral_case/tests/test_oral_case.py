# -*- coding: utf-8 -*-
import base64
import json
import os
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree

from odoo.exceptions import AccessError, MissingError, UserError
from odoo.tests.common import TransactionCase, tagged

from .common import OralCaseFixture


class FakeResponse(object):
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


def _accepted(job_id='job-oral-1'):
    return FakeResponse(202, {
        'ok': True,
        'job_id': job_id,
        'status': 'queued',
        'status_url': 'https://n8n.test/internal-status',
    })


@tagged('post_install', '-at_install')
class TestOralCaseService(OralCaseFixture, TransactionCase):

    def test_enabling_oral_case_keeps_article_html(self):
        self.slide.write({
            'oral_case_enabled': True,
            'oral_case_code': 'DA-ORAL-001',
            'oral_case_survey_id': self.survey.id,
        })
        self.assertEqual(self.slide.slide_category, 'article')
        self.assertEqual(self.slide.html_content, self.html_before)
        if 'html_embed_code' in self.slide._fields:
            self.assertEqual(self.slide.html_embed_code, self.embed_before)

    def test_manifest_ships_the_player_without_replacing_fullscreen(self):
        root = Path(__file__).resolve().parents[1]
        manifest = root.joinpath('__manifest__.py').read_text()
        player = root.joinpath('static', 'src', 'js', 'oral_case_player.js').read_text()
        self.assertNotIn('isep_slide_article_custom', manifest)
        self.assertNotIn('slides_course_fullscreen_player', manifest)
        self.assertNotIn('slides_course_fullscreen_player', player)
        self.assertIn('irg_oral_case/static/src/js/oral_case_player.js', manifest)
        self.assertNotIn('innerHTML', player)
        self.assertIn('textContent', player)
        self.assertIn('MediaRecorder', player)
        self.assertIn('MutationObserver', player)
        self.assertIn('pending_legal_review', player)
        self.assertIn('pendiente de validación legal', player)

    def test_packaged_parameters_do_not_embed_a_key_or_enable_deletion(self):
        root = ElementTree.parse(
            Path(__file__).resolve().parents[1].joinpath('data', 'ir_config_parameter.xml')
        ).getroot()
        values = {}
        for record in root.findall('record'):
            key = value = None
            for field in record.findall('field'):
                if field.get('name') == 'key':
                    key = (field.text or '').strip()
                elif field.get('name') == 'value':
                    value = field.text or ''
            values[key] = value
        self.assertEqual(values['irg_oral_case.api_key'].strip(), '')
        self.assertEqual(values['irg_oral_case.n8n_submit_url'].strip(), '')
        self.assertEqual(values['irg_oral_case.n8n_status_url'].strip(), '')
        self.assertEqual(values['irg_oral_case.retention_enabled'].strip(), 'False')
        self.assertEqual(values['irg_oral_case.retention_days'].strip(), '0')
        self.assertEqual(values['irg_oral_case.store_video_copy'].strip(), 'False')

    def test_partner_from_the_client_is_ignored(self):
        captured = {}

        def fake_post(url, data=None, files=None, headers=None, timeout=None, allow_redirects=None):
            captured['url'] = url
            captured['data'] = data
            captured['headers'] = headers
            captured['allow_redirects'] = allow_redirects
            return _accepted()

        with patch('odoo.addons.irg_oral_case.models.service.requests.post', side_effect=fake_post):
            result = self._service(self.student).submit_recording(
                self.student.partner_id, self._form(), self._video(),
            )
        self.assertEqual(result['http_status'], 202)
        self.assertEqual(captured['data']['partner_id'], str(self.student.partner_id.id))
        self.assertNotEqual(captured['data']['partner_id'], str(self.other_student.partner_id.id))
        self.assertEqual(captured['data']['case_id'], 'DA-ORAL-001')
        self.assertNotIn('mode', captured['data'])
        self.assertNotIn('clips_json', captured['data'])
        self.assertEqual(result['payload']['status'], 'queued')
        self.assertEqual(captured['headers']['X-IRG-Key'], self.api_key)
        self.assertFalse(captured['allow_redirects'])
        self.assertNotIn('https://n8n.test/internal-status', json.dumps(result['payload']))
        self.assertNotIn(self.api_key, json.dumps(result['payload']))
        job = self.env['irg.oral.case.job'].search([
            ('n8n_job_id', '=', 'job-oral-1'),
        ])
        self.assertEqual(job.partner_id, self.student.partner_id)
        self.assertEqual(job.user_input_id.partner_id, self.student.partner_id)
        self.assertEqual(job.user_input_id.state, 'in_progress')
        self.assertNotEqual(job.user_input_id.state, 'done')
        self.assertFalse(job.video_attachment_id)
        self.assertFalse(self.env['app.gradebook.result'].search(self._gradebook_domain()))
        with patch('odoo.addons.irg_oral_case.models.service.requests.post', return_value=_accepted('job-oral-2')):
            again = self._service(self.student).submit_recording(
                self.student.partner_id, self._form(), self._video(),
            )
        self.assertEqual(again['http_status'], 202)
        self.assertEqual(self.env['survey.user_input'].sudo().search_count([
            ('partner_id', '=', self.student.partner_id.id),
            ('slide_id', '=', self.slide.id),
            ('survey_id', '=', self.survey.id),
        ]), 1)

    def test_portal_cannot_create_a_job_for_someone_else(self):
        before = self.env['irg.oral.case.job'].sudo().search_count([])
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'sitemap.xml',
            'datas': base64.b64encode(b'<xml/>'),
            'mimetype': 'application/xml',
            'public': True,
        })
        with self.assertRaises(AccessError):
            self.env['irg.oral.case.job'].with_user(self.internal_user).with_context(
                irg_oral_case_dispatch=True,
            ).create({
                'partner_id': self.other_student.partner_id.id,
                'slide_id': self.slide.id,
                'case_code': 'DA-ORAL-001',
                'consent_date': '2026-10-22 00:00:00',
                'survey_id': self.survey.id,
                'video_attachment_id': attachment.id,
            })
        self.assertEqual(self.env['irg.oral.case.job'].sudo().search_count([]), before)
        self.assertTrue(attachment.exists())

    def test_outsider_cannot_submit(self):
        with patch('odoo.addons.irg_oral_case.models.service.requests.post') as mocked:
            result = self._service(self.other_student).submit_recording(
                self.other_student.partner_id, self._form(), self._video(),
            )
        self.assertEqual(result['payload']['error'], 'slide_forbidden')
        mocked.assert_not_called()

    def test_missing_and_invalid_consent_stop_before_n8n(self):
        with patch('odoo.addons.irg_oral_case.models.service.requests.post') as mocked:
            missing = self._service(self.student).submit_recording(
                self.student.partner_id,
                self._form(consent_date=''),
                self._video(),
            )
            invalid = self._service(self.student).submit_recording(
                self.student.partner_id,
                self._form(consent_date='ayer'),
                self._video(),
            )
        self.assertEqual(missing['payload']['error'], 'missing_consent')
        self.assertEqual(invalid['payload']['error'], 'invalid_consent')
        mocked.assert_not_called()

    def test_size_and_duration_limits(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('irg_oral_case.max_video_bytes', '8')
        params.set_param('irg_oral_case.max_duration_seconds', '5')
        with patch('odoo.addons.irg_oral_case.models.service.requests.post') as mocked:
            too_big = self._service(self.student).submit_recording(
                self.student.partner_id, self._form(duracion_seg='1'), self._video(b'123456789'),
            )
            too_long = self._service(self.student).submit_recording(
                self.student.partner_id, self._form(duracion_seg='6'), self._video(b'1234'),
            )
            bad_duration = self._service(self.student).submit_recording(
                self.student.partner_id, self._form(duracion_seg='-1'), self._video(b'1234'),
            )
        self.assertEqual(too_big['payload']['error'], 'video_too_large')
        self.assertEqual(too_long['payload']['error'], 'duration_exceeded')
        self.assertEqual(bad_duration['payload']['error'], 'invalid_duration')
        mocked.assert_not_called()

    def test_invalid_self_assessment_and_video_type(self):
        with patch('odoo.addons.irg_oral_case.models.service.requests.post') as mocked:
            bad_json = self._service(self.student).submit_recording(
                self.student.partner_id,
                self._form(autoevaluacion_json='no-json'),
                self._video(),
            )
            bad_type = self._service(self.student).submit_recording(
                self.student.partner_id,
                self._form(),
                self._video(content_type='text/html', filename='caso.html'),
            )
        self.assertEqual(bad_json['payload']['error'], 'invalid_self_assessment')
        self.assertEqual(bad_type['payload']['error'], 'invalid_video_type')
        mocked.assert_not_called()

    def test_n8n_error_redacts_the_key_and_does_not_grade(self):
        def fake_post(url, data=None, files=None, headers=None, timeout=None, allow_redirects=None):
            return FakeResponse(400, {
                'ok': False,
                'errors': ['rechazado %s' % headers['X-IRG-Key']],
            })

        with patch('odoo.addons.irg_oral_case.models.service.requests.post', side_effect=fake_post):
            result = self._service(self.student).submit_recording(
                self.student.partner_id, self._form(), self._video(),
            )
        self.assertEqual(result['http_status'], 400)
        self.assertEqual(result['payload']['error'], 'n8n_rejected')
        self.assertNotIn(self.api_key, json.dumps(result['payload']))
        self.assertIn('***', result['payload']['errors'][0])
        self.assertFalse(self.env['app.gradebook.result'].search(self._gradebook_domain()))

    def test_environment_overrides_parameters_without_leaking(self):
        captured = {}

        def fake_post(url, data=None, files=None, headers=None, timeout=None, allow_redirects=None):
            captured['url'] = url
            captured['key'] = headers['X-IRG-Key']
            return _accepted('job-env-1')

        with patch.dict(os.environ, {
            'IRG_ORAL_CASE_API_KEY': 'env-oral-key',
            'IRG_ORAL_CASE_N8N_SUBMIT_URL': 'https://n8n.test/from-env',
        }), patch('odoo.addons.irg_oral_case.models.service.requests.post', side_effect=fake_post):
            result = self._service(self.student).submit_recording(
                self.student.partner_id, self._form(), self._video(),
            )
        self.assertEqual(captured['url'], 'https://n8n.test/from-env')
        self.assertEqual(captured['key'], 'env-oral-key')
        self.assertNotIn('env-oral-key', json.dumps(result['payload']))

    def test_status_is_limited_to_the_owner_and_drops_extra_fields(self):
        participation = self._participation(self.student.partner_id)
        job = self.env['irg.oral.case.job'].create({
            'partner_id': self.student.partner_id.id,
            'slide_id': self.slide.id,
            'survey_id': self.survey.id,
            'user_input_id': participation.id,
            'case_code': 'DA-ORAL-001',
            'consent_date': '2026-10-22 00:00:00',
            'n8n_job_id': 'job-status-1',
            'state': 'accepted',
        })

        def fake_get(url, params=None, headers=None, timeout=None, allow_redirects=None):
            return FakeResponse(200, {
                'job_id': 'job-status-1',
                'status': 'done',
                'score_ia': 7.5,
                'duracion_fuera_rango': True,
                'user_input_id': 999999,
                'error': 'fallo %s' % headers['X-IRG-Key'],
                'updated_at': '2026-10-22T12:00:00',
                'api_key': headers['X-IRG-Key'],
            })

        with patch('odoo.addons.irg_oral_case.models.service.requests.get', side_effect=fake_get) as mocked:
            foreign = self._service(self.other_student).fetch_status(
                self.other_student.partner_id, job.n8n_job_id,
            )
            self.assertEqual(foreign['payload']['error'], 'job_not_found')
            mocked.assert_not_called()
            own = self._service(self.student).fetch_status(
                self.student.partner_id, job.n8n_job_id,
            )
        self.assertEqual(own['http_status'], 200)
        self.assertEqual(own['payload']['user_input_id'], participation.id)
        self.assertEqual(own['payload']['score_ia'], 7.5)
        self.assertNotIn(self.api_key, json.dumps(own['payload']))
        self.assertNotIn('api_key', own['payload'])
        self.assertFalse(self.env['app.gradebook.result'].search(self._gradebook_domain()))
        hidden = self.env['irg.oral.case.job'].with_user(self.other_student).search([
            ('id', '=', job.id),
        ])
        self.assertFalse(hidden)

    def test_api_key_is_not_rendered_in_views(self):
        views = self.env['ir.ui.view'].sudo().search([
            ('arch_db', 'ilike', self.api_key),
        ])
        self.assertFalse(views)

    def _participation(self, partner):
        return self.env['survey.user_input'].sudo().create({
            'survey_id': self.survey.id,
            'partner_id': partner.id,
            'slide_id': self.slide.id,
            'state': 'in_progress',
        })


@tagged('post_install', '-at_install')
class TestOralCaseGrade(OralCaseFixture, TransactionCase):

    def setUp(self):
        super().setUp()
        self.participation = self.env['survey.user_input'].sudo().create({
            'survey_id': self.survey.id,
            'partner_id': self.student.partner_id.id,
            'slide_id': self.slide.id,
            'state': 'in_progress',
            'score_ia': 9.0,
            'resumen_ia': 'Sugerencia de la IA',
            'error_ai': False,
        })

    def test_student_cannot_write_the_suggestion_or_the_official_grade(self):
        self._assert_access_blocked(
            lambda: self.participation.with_user(self.student).write({'score_ia': 10})
        )
        with self.assertRaises(AccessError):
            self.env['irg.oral.case.confirm.grade'].with_user(self.student).create({
                'user_input_id': self.participation.id,
                'official_score': 10,
                'confirm_official': True,
            })
        with self.assertRaises(AccessError):
            self.env['app.gradebook.result'].with_user(self.student).create({
                'scoring_total': 10,
                'survey_type': 'exam',
                'survey_user_input_id': self.participation.id,
                'channel_id': self.channel.id,
            })
        self.assertFalse(self.env['app.gradebook.result'].search(self._gradebook_domain()))

    def test_internal_user_without_faculty_cannot_confirm(self):
        wizard = self.env['irg.oral.case.confirm.grade'].with_user(self.teacher).create({
            'user_input_id': self.participation.id,
            'official_score': 8,
            'confirm_official': True,
        })
        with self.assertRaises(AccessError):
            wizard.with_user(self.internal_user).action_confirm()
        self.assertFalse(self.env['app.gradebook.result'].search(self._gradebook_domain()))

    def test_teacher_confirmation_is_required_and_does_not_copy_the_suggestion(self):
        if 'is_published' in self.channel._fields:
            self.channel.write({'is_published': False})
        pending = self.env['irg.oral.case.confirm.grade'].with_user(self.teacher).create({
            'user_input_id': self.participation.id,
            'official_score': 6,
            'confirm_official': False,
        })
        self.assertEqual(pending.score_ia, 9.0)
        self.assertEqual(pending.official_score, 6)
        with self.assertRaises(UserError):
            pending.action_confirm()
        self.assertFalse(self.env['app.gradebook.result'].search(self._gradebook_domain()))

        confirmed = self.env['irg.oral.case.confirm.grade'].with_user(self.teacher).create({
            'user_input_id': self.participation.id,
            'official_score': 6,
            'confirm_official': True,
            'comment': 'Nota del docente',
        })
        confirmed.action_confirm()
        result = self.env['app.gradebook.result'].search(self._gradebook_domain())
        self.assertEqual(len(result), 1)
        self.assertEqual(result.scoring_total, 6.0)
        self.assertEqual(result.rated_by, self.teacher.partner_id)
        self.assertEqual(result.survey_user_input_id, self.participation)
        self.assertFalse(self.participation.result_id)
        self.participation.with_user(self.teacher).write({'score_ia': 1.0})
        result.invalidate_recordset(['scoring_total'])
        self.assertEqual(result.scoring_total, 6.0)


@tagged('post_install', '-at_install')
class TestOralCaseRetention(OralCaseFixture, TransactionCase):

    def test_cron_does_not_delete_until_the_policy_is_enabled(self):
        job = self.env['irg.oral.case.job'].create({
            'partner_id': self.student.partner_id.id,
            'slide_id': self.slide.id,
            'survey_id': self.survey.id,
            'case_code': 'DA-ORAL-001',
            'consent_date': '2020-01-01 00:00:00',
        })
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'caso.webm',
            'datas': base64.b64encode(b'webm'),
            'res_model': 'irg.oral.case.job',
            'res_id': job.id,
            'mimetype': 'video/webm',
            'public': False,
        })
        job.write({
            'video_attachment_id': attachment.id,
            'video_stored_at': '2020-01-01 00:00:00',
        })
        self.assertFalse(self.env['irg.oral.case.job']._cron_apply_video_retention())
        self.assertTrue(attachment.exists())

        params = self.env['ir.config_parameter'].sudo()
        params.set_param('irg_oral_case.retention_enabled', 'True')
        params.set_param('irg_oral_case.retention_days', '0')
        self.assertFalse(self.env['irg.oral.case.job']._cron_apply_video_retention())
        self.assertTrue(attachment.exists())

        params.set_param('irg_oral_case.retention_days', '30')
        with patch.object(
            type(self.env['irg.oral.case.job']),
            '_irg_module_operation_in_progress',
            return_value=True,
        ):
            self.assertFalse(self.env['irg.oral.case.job']._cron_apply_video_retention())
        self.assertTrue(attachment.exists())

        self.assertTrue(self.env['irg.oral.case.job']._cron_apply_video_retention())
        self.assertFalse(attachment.exists())
        job.invalidate_recordset()
        self.assertTrue(job.video_purged)
        self.assertFalse(job.video_attachment_id)

    def test_cron_does_not_delete_a_foreign_attachment(self):
        foreign = self.env['ir.attachment'].sudo().create({
            'name': 'sitemap.xml',
            'datas': base64.b64encode(b'<xml/>'),
            'res_model': 'ir.ui.view',
            'res_id': 1,
            'mimetype': 'application/xml',
            'public': True,
        })
        job = self.env['irg.oral.case.job'].create({
            'partner_id': self.student.partner_id.id,
            'slide_id': self.slide.id,
            'survey_id': self.survey.id,
            'case_code': 'DA-ORAL-001',
            'consent_date': '2020-01-01 00:00:00',
            'video_attachment_id': foreign.id,
            'video_stored_at': '2020-01-01 00:00:00',
        })
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('irg_oral_case.retention_enabled', 'True')
        params.set_param('irg_oral_case.retention_days', '30')
        self.assertTrue(self.env['irg.oral.case.job']._cron_apply_video_retention())
        self.assertTrue(foreign.exists())
        job.invalidate_recordset()
        self.assertFalse(job.video_attachment_id)
        self.assertTrue(job.video_purged)
