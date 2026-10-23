# -*- coding: utf-8 -*-
import base64
import json
from unittest.mock import patch

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import HttpCase, TransactionCase, tagged

from .common import OralCaseFixture
from .test_oral_case import FakeResponse, _accepted


@tagged('post_install', '-at_install')
class TestOralCaseClips(OralCaseFixture, TransactionCase):

    def setUp(self):
        super().setUp()
        self.slide.oral_case_mode = 'clips'
        self.first = self.env['irg.oral.case.segment'].create({
            'slide_id': self.slide.id,
            'sequence': 1,
            'name': 'Apertura',
            'clip_url': 'https://cdn.example.test/paciente-01.mp4',
            'prompt': '¿Qué observa en la apertura?',
            'max_seconds': 30,
            'allow_retry': True,
        })
        self.second = self.env['irg.oral.case.segment'].create({
            'slide_id': self.slide.id,
            'sequence': 2,
            'name': 'Cierre',
            'clip_url': 'https://player.vimeo.com/video/123?h=abc',
            'prompt': '¿Cómo cierra la entrevista?',
            'max_seconds': 20,
            'allow_retry': False,
        })

    def test_segment_url_must_be_https_without_userinfo(self):
        with self.assertRaises(ValidationError):
            self.env['irg.oral.case.segment'].create({
                'slide_id': self.slide.id,
                'name': 'Malo',
                'clip_url': 'javascript:alert(1)',
                'prompt': 'No',
                'max_seconds': 10,
            })
        with self.assertRaises(ValidationError):
            self.first.write({'clip_url': 'https://user:secret@player.vimeo.com/video/1'})

    def test_student_cannot_create_a_segment(self):
        with self.assertRaises(AccessError):
            self.env['irg.oral.case.segment'].with_user(self.student).create({
                'slide_id': self.slide.id,
                'name': 'Ajeno',
                'clip_url': 'https://cdn.example.test/x.mp4',
                'prompt': 'No',
                'max_seconds': 10,
            })

    def test_clips_are_sent_with_the_server_prompt(self):
        captured = {}

        def fake_post(url, data=None, files=None, headers=None, timeout=None, allow_redirects=None):
            captured['data'] = data
            captured['files'] = files
            return _accepted('job-clips-1')

        form = self._form(clips_json=json.dumps([
            {'index': 1, 'segment_id': self.first.id, 'duration_seconds': 10, 'prompt': 'HACK'},
            {'index': 2, 'segment_id': self.second.id, 'duration_seconds': 8},
        ]))
        with patch('odoo.addons.irg_oral_case.models.service.requests.post', side_effect=fake_post):
            result = self._service(self.student).submit_recording(
                self.student.partner_id,
                form,
                None,
                {
                    'clip_1': self._video(b'clip-uno', filename='uno.webm'),
                    'clip_2': self._video(b'clip-dos', filename='dos.webm'),
                },
            )
        self.assertEqual(result['http_status'], 202)
        self.assertEqual(result['payload']['status'], 'queued')
        self.assertEqual(captured['data']['mode'], 'clips')
        self.assertEqual(captured['data']['case_id'], 'DA-ORAL-001')
        meta = json.loads(captured['data']['clips_json'])
        self.assertEqual(meta[0]['prompt'], '¿Qué observa en la apertura?')
        self.assertEqual(meta[0]['clip_url'], 'https://cdn.example.test/paciente-01.mp4')
        self.assertEqual(meta[1]['index'], 2)
        self.assertIn('clip_1', captured['files'])
        self.assertIn('clip_2', captured['files'])
        self.assertNotIn('video', captured['files'])
        job = self.env['irg.oral.case.job'].search([('n8n_job_id', '=', 'job-clips-1')])
        self.assertEqual(len(job.clip_ids), 2)
        self.assertEqual(job.clip_ids.sorted('segment_index')[0].prompt_snapshot, meta[0]['prompt'])

    def test_wrong_clip_order_does_not_call_n8n(self):
        form = self._form(clips_json=json.dumps([
            {'index': 2, 'segment_id': self.second.id, 'duration_seconds': 8},
            {'index': 1, 'segment_id': self.first.id, 'duration_seconds': 10},
        ]))
        with patch('odoo.addons.irg_oral_case.models.service.requests.post') as mocked:
            result = self._service(self.student).submit_recording(
                self.student.partner_id,
                form,
                None,
                {
                    'clip_1': self._video(b'a'),
                    'clip_2': self._video(b'b'),
                },
            )
        self.assertEqual(result['payload']['error'], 'clips_mismatch')
        mocked.assert_not_called()

    def test_clip_duration_above_the_segment_is_rejected(self):
        form = self._form(clips_json=json.dumps([
            {'index': 1, 'segment_id': self.first.id, 'duration_seconds': 10},
            {'index': 2, 'segment_id': self.second.id, 'duration_seconds': 21},
        ]))
        with patch('odoo.addons.irg_oral_case.models.service.requests.post') as mocked:
            result = self._service(self.student).submit_recording(
                self.student.partner_id,
                form,
                None,
                {
                    'clip_1': self._video(b'a'),
                    'clip_2': self._video(b'b'),
                },
            )
        self.assertEqual(result['payload']['error'], 'duration_exceeded')
        mocked.assert_not_called()

    def test_single_mode_rejects_clips_and_keeps_one_video(self):
        self.slide.oral_case_mode = 'single'
        with patch('odoo.addons.irg_oral_case.models.service.requests.post') as mocked:
            rejected = self._service(self.student).submit_recording(
                self.student.partner_id,
                self._form(clips_json='[]'),
                None,
                {'clip_1': self._video(b'a')},
            )
        self.assertEqual(rejected['payload']['error'], 'single_video_expected')
        mocked.assert_not_called()

    def test_processing_from_n8n_is_published_as_queued(self):
        def fake_post(url, data=None, files=None, headers=None, timeout=None, allow_redirects=None):
            return FakeResponse(202, {'ok': True, 'job_id': 'job-proc-1', 'status': 'processing'})

        self.slide.oral_case_mode = 'single'
        with patch('odoo.addons.irg_oral_case.models.service.requests.post', side_effect=fake_post):
            result = self._service(self.student).submit_recording(
                self.student.partner_id, self._form(), self._video(),
            )
        self.assertEqual(result['payload']['status'], 'queued')
        job = self.env['irg.oral.case.job'].search([('n8n_job_id', '=', 'job-proc-1')])
        self.assertEqual(job.n8n_status, 'processing')

    def test_slide_flag_stores_the_clip_and_global_flag_still_does(self):
        self.slide.oral_case_keep_video = True
        with patch('odoo.addons.irg_oral_case.models.service.requests.post', return_value=_accepted('job-keep-1')):
            self._service(self.student).submit_recording(
                self.student.partner_id,
                self._form(clips_json=json.dumps([
                    {'index': 1, 'segment_id': self.first.id, 'duration_seconds': 5},
                    {'index': 2, 'segment_id': self.second.id, 'duration_seconds': 5},
                ])),
                None,
                {'clip_1': self._video(b'aaaa'), 'clip_2': self._video(b'bbbb')},
            )
        job = self.env['irg.oral.case.job'].search([('n8n_job_id', '=', 'job-keep-1')])
        stored = job.clip_ids.mapped('video_attachment_id')
        self.assertEqual(len(stored), 2)
        for attachment in stored:
            self.assertEqual(attachment.mimetype, 'video/webm')
            self.assertFalse(attachment.public)
            self.assertEqual(attachment.res_model, 'irg.oral.case.clip')
        self.assertTrue(job.video_kept)

    def test_status_stores_scores_per_segment_and_not_the_official_grade(self):
        participation = self.env['survey.user_input'].sudo().create({
            'survey_id': self.survey.id,
            'partner_id': self.student.partner_id.id,
            'slide_id': self.slide.id,
            'state': 'in_progress',
        })
        job = self.env['irg.oral.case.job'].create({
            'partner_id': self.student.partner_id.id,
            'slide_id': self.slide.id,
            'survey_id': self.survey.id,
            'user_input_id': participation.id,
            'case_code': 'DA-ORAL-001',
            'consent_date': '2026-10-22 00:00:00',
            'n8n_job_id': 'job-tramos-1',
            'state': 'accepted',
        })
        clip = self.env['irg.oral.case.clip'].sudo().create({
            'job_id': job.id,
            'segment_id': self.first.id,
            'segment_index': 1,
            'prompt_snapshot': self.first.prompt,
        })

        def fake_get(url, params=None, headers=None, timeout=None, allow_redirects=None):
            return FakeResponse(200, {
                'status': 'done',
                'score_ia': 7.5,
                'resumen_ia': 'Propuesta global',
                'official_score': 10,
                'tramos': [{'index': 1, 'score_ia': 8, 'resumen_ia': 'Ve el síntoma'}],
            })

        with patch('odoo.addons.irg_oral_case.models.service.requests.get', side_effect=fake_get):
            result = self._service(self.student).fetch_status(self.student.partner_id, job.n8n_job_id)
        self.assertEqual(result['payload']['tramos'][0]['score_ia'], 8)
        self.assertNotIn(self.api_key, json.dumps(result['payload']))
        clip.invalidate_recordset()
        participation.invalidate_recordset()
        job.invalidate_recordset()
        self.assertEqual(clip.score_ia, 8)
        self.assertEqual(participation.score_ia, 7.5)
        self.assertEqual(job.official_score, 0)
        self.assertFalse(job.gradebook_result_id)

    def test_cannot_resubmit_after_the_official_grade(self):
        participation = self.env['survey.user_input'].sudo().create({
            'survey_id': self.survey.id,
            'partner_id': self.student.partner_id.id,
            'slide_id': self.slide.id,
            'state': 'in_progress',
        })
        self.env['irg.oral.case.job'].create({
            'partner_id': self.student.partner_id.id,
            'slide_id': self.slide.id,
            'survey_id': self.survey.id,
            'user_input_id': participation.id,
            'case_code': 'DA-ORAL-001',
            'consent_date': '2026-10-22 00:00:00',
            'official_confirmed_at': '2026-10-22 12:00:00',
            'official_score': 6,
        })
        with patch('odoo.addons.irg_oral_case.models.service.requests.post') as mocked:
            result = self._service(self.student).submit_recording(
                self.student.partner_id, self._form(), self._video(),
            )
        self.assertEqual(result['payload']['error'], 'grade_already_confirmed')
        mocked.assert_not_called()


@tagged('post_install', '-at_install')
class TestOralCaseGradeSecurity(OralCaseFixture, TransactionCase):

    def setUp(self):
        super().setUp()
        self.participation = self.env['survey.user_input'].sudo().create({
            'survey_id': self.survey.id,
            'partner_id': self.student.partner_id.id,
            'slide_id': self.slide.id,
            'state': 'in_progress',
            'score_ia': 9.0,
        })
        self.other_input = self.env['survey.user_input'].sudo().create({
            'survey_id': self.survey.id,
            'partner_id': self.other_student.partner_id.id,
            'slide_id': self.slide.id,
            'state': 'in_progress',
        })
        self.job = self.env['irg.oral.case.job'].create({
            'partner_id': self.student.partner_id.id,
            'slide_id': self.slide.id,
            'survey_id': self.survey.id,
            'user_input_id': self.participation.id,
            'case_code': 'DA-ORAL-001',
            'consent_date': '2026-10-22 00:00:00',
            'state': 'accepted',
        })
        self.foreign_result = self.env['app.gradebook.result'].create({
            'survey_user_input_id': self.other_input.id,
            'scoring_total': 3,
            'survey_type': 'exam',
            'channel_id': self.channel.id,
            'description': 'Línea ajena',
        })
        self.foreign_attachment = self.env['ir.attachment'].sudo().create({
            'name': 'website.assets_wysiwyg.js',
            'datas': base64.b64encode(b'js'),
            'mimetype': 'application/javascript',
            'public': True,
        })

    def test_teacher_and_student_cannot_reassign_technical_links(self):
        attacks = [
            {'gradebook_result_id': self.foreign_result.id},
            {'video_attachment_id': self.foreign_attachment.id},
            {'official_confirmed_by': self.teacher.id},
            {'official_confirmed_at': '2026-10-22 12:00:00'},
            {'video_stored_at': '2026-10-22 12:00:00'},
            {'user_input_id': self.other_input.id},
            {'partner_id': self.other_student.partner_id.id},
        ]
        for vals in attacks:
            for ctx in ({}, {'irg_oral_case_system': True}, {'irg_oral_case_dispatch': True}):
                with self.assertRaises(AccessError):
                    self.job.with_user(self.teacher).with_context(**ctx).write(vals)
                with self.assertRaises(AccessError):
                    self.job.with_user(self.student).with_context(**ctx).write(vals)
        self.assertFalse(self.job.gradebook_result_id)
        self.assertFalse(self.job.video_attachment_id)
        self.assertFalse(self.job.official_confirmed_by)
        self.assertEqual(self.job.user_input_id, self.participation)
        self.assertEqual(self.foreign_result.scoring_total, 3)
        before = self.env['irg.oral.case.job'].sudo().search_count([])
        with self.assertRaises(AccessError):
            self.env['irg.oral.case.job'].with_user(self.student).with_context(
                irg_oral_case_system=True,
            ).create({
                'partner_id': self.student.partner_id.id,
                'slide_id': self.slide.id,
                'case_code': 'DA-ORAL-001',
                'consent_date': '2026-10-22 00:00:00',
                'user_input_id': self.other_input.id,
                'video_attachment_id': self.foreign_attachment.id,
                'gradebook_result_id': self.foreign_result.id,
            })
        self.assertEqual(self.env['irg.oral.case.job'].sudo().search_count([]), before)

    def test_numeric_grade_writes_only_this_students_line(self):
        self.job.with_user(self.teacher).write({
            'official_score': 6,
            'official_score_reason': 'criterio clínico',
        })
        self.assertEqual(self.job.official_score, 6)
        self.assertEqual(self.job.official_confirmed_by, self.teacher)
        result = self.job.gradebook_result_id
        self.assertTrue(result)
        self.assertEqual(result.survey_user_input_id, self.participation)
        self.assertEqual(result.scoring_total, 6)
        self.assertEqual(result.rated_by, self.teacher.partner_id)
        self.assertEqual(result.write_uid, self.teacher)
        self.assertNotEqual(result, self.foreign_result)
        self.assertEqual(self.foreign_result.scoring_total, 3)
        self.assertEqual(self.participation.score_ia, 9)
        self.assertFalse(self.participation.result_id)
        bodies = ' '.join(self.job.sudo().message_ids.mapped('body'))
        self.assertIn('sin nota', bodies)
        self.assertIn('6.0', bodies)
        self.assertIn(self.teacher.name, bodies)
        self.assertIn('criterio clínico', bodies)
        self.assertNotIn('<script', bodies.lower())

        self.job.with_user(self.teacher).write({'official_score': 8})
        self.assertEqual(self.job.gradebook_result_id, result)
        self.assertEqual(result.scoring_total, 8)
        self.assertEqual(result.write_uid, self.teacher)
        self.assertEqual(self.foreign_result.scoring_total, 3)
        bodies = ' '.join(self.job.sudo().message_ids.mapped('body'))
        self.assertIn('8.0', bodies)

        with self.assertRaises(ValidationError):
            self.job.with_user(self.teacher).write({'official_score': 11})
        with self.assertRaises(ValidationError):
            self.job.with_user(self.teacher).write({'official_score': -1})
        self.assertEqual(self.job.official_score, 8)
        self.assertEqual(result.scoring_total, 8)

    def test_empty_subject_partner_does_not_receive_the_grade(self):
        subject = self.env['app.gradebook.subject'].sudo().create({})
        self.assertFalse(subject.partner_id)
        wizard = self.env['irg.oral.case.confirm.grade'].with_user(self.teacher).create({
            'user_input_id': self.participation.id,
            'official_score': 7,
            'confirm_official': True,
            'gradebook_subject_id': subject.id,
        })
        with self.assertRaises(AccessError):
            wizard.action_confirm()
        self.assertFalse(self.job.gradebook_result_id)
        self.assertEqual(self.foreign_result.scoring_total, 3)

    def test_non_superuser_cannot_plant_a_gradebook_line_on_an_oral_case(self):
        manager = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'Gestor de encuestas',
            'login': 'oral-survey-%s' % self.student_login,
            'password': 'oral-survey-manager',
            'groups_id': [(6, 0, [self.env.ref('survey.group_survey_manager').id])],
        })
        with self.assertRaises(AccessError):
            self.env['survey.user_input'].with_user(manager).create({
                'survey_id': self.survey.id,
                'partner_id': self.student.partner_id.id,
                'slide_id': self.slide.id,
                'state': 'in_progress',
                'result_id': self.foreign_result.id,
            })
        self.assertEqual(self.foreign_result.scoring_total, 3)
        plain = self.env['slide.slide'].create({
            'name': 'Artículo sin caso',
            'channel_id': self.channel.id,
            'slide_category': 'article',
            'is_published': True,
            'html_content': '<p>sin caso</p>',
            'oral_case_enabled': False,
        })
        plain_input = self.env['survey.user_input'].sudo().create({
            'survey_id': self.survey.id,
            'partner_id': self.student.partner_id.id,
            'slide_id': plain.id,
            'state': 'in_progress',
            'result_id': self.foreign_result.id,
        })
        score_after_plain = self.foreign_result.scoring_total
        with self.assertRaises(AccessError):
            plain_input.with_user(manager).write({
                'slide_id': self.slide.id,
                'result_id': self.foreign_result.id,
            })
        with self.assertRaises(AccessError):
            plain_input.with_user(manager).write({'slide_id': self.slide.id})
        self.assertEqual(plain_input.slide_id, plain)
        self.assertEqual(plain_input.result_id, self.foreign_result)
        self.assertEqual(self.foreign_result.scoring_total, score_after_plain)


    def test_teacher_cannot_retarget_the_participation(self):
        with self.assertRaises(AccessError):
            self.participation.with_user(self.teacher).write({
                'partner_id': self.other_student.partner_id.id,
            })
        with self.assertRaises(AccessError):
            self.participation.with_user(self.teacher).write({
                'result_id': self.foreign_result.id,
            })
        self.assertEqual(self.participation.partner_id, self.student.partner_id)
        self.assertFalse(self.participation.result_id)

    def test_teacher_cannot_retarget_a_clip_attachment(self):
        clip = self.env['irg.oral.case.clip'].sudo().create({
            'job_id': self.job.id,
            'segment_index': 1,
            'prompt_snapshot': 'Consigna',
        })
        with self.assertRaises(AccessError):
            clip.with_user(self.teacher).write({
                'video_attachment_id': self.foreign_attachment.id,
            })
        with self.assertRaises(AccessError):
            self.env['irg.oral.case.clip'].with_user(self.student).create({
                'job_id': self.job.id,
                'segment_index': 2,
            })
        self.assertFalse(clip.video_attachment_id)


@tagged('post_install', '-at_install')
class TestOralCaseMedia(OralCaseFixture, HttpCase):

    def test_media_route_serves_only_the_case_video(self):
        participation = self.env['survey.user_input'].sudo().create({
            'survey_id': self.survey.id,
            'partner_id': self.student.partner_id.id,
            'slide_id': self.slide.id,
            'state': 'in_progress',
        })
        job = self.env['irg.oral.case.job'].create({
            'partner_id': self.student.partner_id.id,
            'slide_id': self.slide.id,
            'survey_id': self.survey.id,
            'user_input_id': participation.id,
            'case_code': 'DA-ORAL-001',
            'consent_date': '2026-10-22 00:00:00',
        })
        payload = b'\x1a\x45\xdf\xa3webm-propio'
        attachment = self.env['ir.attachment'].sudo().create({
            'name': 'caso.webm',
            'datas': base64.b64encode(payload),
            'res_model': 'irg.oral.case.job',
            'res_id': job.id,
            'mimetype': 'video/webm',
            'public': False,
        })
        job.write({'video_attachment_id': attachment.id})
        foreign = self.env['ir.attachment'].sudo().create({
            'name': 'sitemap.xml',
            'datas': base64.b64encode(b'<xml/>'),
            'res_model': 'ir.ui.view',
            'res_id': 1,
            'mimetype': 'text/xml',
            'public': True,
        })
        self.authenticate(self.student_login, self.student_login)
        own = self.url_open('/irg/oral_case/media/job/%s' % job.id)
        self.assertEqual(own.status_code, 200)
        self.assertEqual(own.headers.get('Content-Type'), 'video/webm')
        self.assertIn('nosniff', own.headers.get('X-Content-Type-Options', ''))
        self.assertEqual(own.content, payload)
        self.assertNotIn('web/content', own.headers.get('Location', ''))

        self.authenticate(self.other_login, self.other_login)
        hidden = self.url_open('/irg/oral_case/media/job/%s' % job.id, allow_redirects=False)
        self.assertEqual(hidden.status_code, 404)
        self.assertNotIn(b'webm-propio', hidden.content)

        job.sudo().write({'video_attachment_id': foreign.id})
        self.authenticate(self.teacher_login, self.teacher_login)
        blocked = self.url_open('/irg/oral_case/media/job/%s' % job.id, allow_redirects=False)
        self.assertEqual(blocked.status_code, 404)
        self.assertTrue(foreign.exists())
