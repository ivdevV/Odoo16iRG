import re

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests.common import HttpCase, TransactionCase, tagged

from .test_tfm_deliveries import TfmFixtureMixin


@tagged('post_install', '-at_install')
class TestTfmOutlineSurvey(TfmFixtureMixin, TransactionCase):
    def setUp(self):
        super().setUp()
        self.survey = self.env.ref('irg_tfm_convocatorias.tfm_outline_survey')

    def _question(self, prefill_source=None, title=None):
        questions = self.survey.question_ids.filtered(lambda item: not item.is_page)
        if prefill_source:
            questions = questions.filtered(
                lambda item: item.irg_tfm_prefill_source == prefill_source
            )
        if title:
            questions = questions.filtered(lambda item: item.title == title)
        self.assertEqual(len(questions), 1)
        return questions

    def _start(self):
        user, student, course, enrollment, thesis = self._portal_case()
        Outline = self.env['irg.tfm.esquema'].with_user(user)
        outline = Outline._irg_portal_start(course.id)
        return user, student, course, enrollment, thesis, outline

    def _fill_required(self, user, course, outline):
        service = self.env['irg.tfm.esquema'].with_user(user)
        for step_key in ('proposal', 'approach', 'results'):
            answers = {}
            for question in outline.question_ids.filtered(
                lambda item: item.step_key == step_key and item.mandatory
            ):
                if question.question_type in ('simple_choice', 'multiple_choice'):
                    answers[str(question.id)] = [question.option_ids[0].id]
                elif not question.answer_text:
                    answers[str(question.id)] = 'Respuesta válida'
            outline = service._irg_portal_save_step(
                course.id,
                outline.id,
                step_key,
                outline.revision,
                answers,
            )
        return outline

    def test_default_template_has_three_stable_steps_and_ten_questions(self):
        pages = self.survey.question_and_page_ids.filtered('is_page')
        questions = self.survey.question_and_page_ids - pages
        self.assertEqual(
            set(pages.mapped('irg_tfm_step_key')),
            {'proposal', 'approach', 'results'},
        )
        self.assertEqual(len(pages), 3)
        self.assertEqual(len(questions), 10)
        self.assertEqual(
            set(questions.mapped('irg_tfm_prefill_source')) - {False},
            {'student_name', 'student_email', 'master_name'},
        )
        self.assertEqual(self.survey.questions_layout, 'page_per_section')

    def test_start_freezes_template_and_prefills_editable_student_data(self):
        user, student, course, _enrollment, _thesis, outline = self._start()
        self.assertEqual(outline.state, 'draft')
        self.assertEqual(outline.version, 0)
        self.assertEqual(outline.revision, 0)
        self.assertEqual(len(outline.question_ids), 10)
        name = outline.question_ids.filtered(
            lambda item: item.prefill_source == 'student_name'
        )
        email = outline.question_ids.filtered(
            lambda item: item.prefill_source == 'student_email'
        )
        master = outline.question_ids.filtered(
            lambda item: item.prefill_source == 'master_name'
        )
        self.assertEqual(name.answer_text, student.name)
        self.assertEqual(email.answer_text, student.email)
        self.assertEqual(master.answer_text, course.name)

        source = self._question(prefill_source='student_name')
        frozen_title = name.title
        source.write({'title': 'Edited after draft start'})
        self.assertEqual(name.title, frozen_title)
        self.assertEqual(
            self.env['irg.tfm.esquema'].with_user(user)._irg_portal_start(course.id),
            outline,
        )

    def test_editable_section_title_is_frozen_for_portal_display(self):
        page = self.env.ref('irg_tfm_convocatorias.tfm_outline_page_proposal')
        page.write({'title': 'Mi propuesta personalizada'})
        _user, _student, _course, _enrollment, _thesis, outline = self._start()
        proposal = outline.question_ids.filtered(
            lambda item: item.step_key == 'proposal'
        )
        self.assertTrue(proposal)
        self.assertEqual(set(proposal.mapped('section_title')), {
            'Mi propuesta personalizada',
        })

    def test_invalid_template_returns_only_generic_portal_error(self):
        user, _student, course, _enrollment, _thesis = self._portal_case()
        invalid = self.env['survey.survey'].create({
            'title': 'Plantilla TFM incompleta',
            'questions_layout': 'page_per_section',
            'irg_tfm_template_only': True,
        })
        self.env['ir.config_parameter'].sudo().set_param(
            'irg_tfm_convocatorias.outline_survey_id', invalid.id,
        )
        with self.assertRaisesRegex(
            ValidationError, 'no está disponible temporalmente',
        ) as caught:
            self.env['irg.tfm.esquema'].with_user(user)._irg_portal_start(course.id)
        self.assertNotIn('pasos', str(caught.exception))
        self.assertNotIn('preguntas', str(caught.exception))

    def test_save_step_accepts_edits_and_rejects_stale_revision(self):
        user, _student, course, _enrollment, _thesis, outline = self._start()
        title = outline.question_ids.filtered(
            lambda item: item.title == 'Título provisional del TFM'
        )
        modality = outline.question_ids.filtered(
            lambda item: item.title == 'Modalidad del TFM'
        )
        saved = self.env['irg.tfm.esquema'].with_user(user)._irg_portal_save_step(
            course.id,
            outline.id,
            'proposal',
            0,
            {
                str(title.id): 'Título editable',
                str(modality.id): [modality.option_ids[0].id],
            },
            advance=True,
        )
        self.assertEqual(saved.revision, 1)
        self.assertEqual(saved.current_step, 'approach')
        self.assertEqual(title.answer_text, 'Título editable')
        with self.assertRaisesRegex(ValidationError, 'otra pestaña'):
            self.env['irg.tfm.esquema'].with_user(user)._irg_portal_save_step(
                course.id,
                outline.id,
                'proposal',
                0,
                {str(title.id): 'Sobrescritura obsoleta'},
            )
        self.assertEqual(title.answer_text, 'Título editable')

    def test_option_must_belong_to_frozen_question(self):
        user, _student, course, _enrollment, _thesis, outline = self._start()
        question = outline.question_ids.filtered(
            lambda item: item.question_type in ('simple_choice', 'multiple_choice')
        )
        other_user, _student, other_course, _enrollment, _thesis, other = self._start()
        other_question = other.question_ids.filtered(
            lambda item: item.question_type in ('simple_choice', 'multiple_choice')
        )
        with self.assertRaises(ValidationError):
            self.env['irg.tfm.esquema'].with_user(user)._irg_portal_save_step(
                course.id,
                outline.id,
                question.step_key,
                outline.revision,
                {str(question.id): [other_question.option_ids[0].id]},
            )
        self.assertNotEqual(user, other_user)
        self.assertNotEqual(course, other_course)

    def test_answer_and_total_size_limits_are_enforced_before_writing(self):
        user, _student, course, _enrollment, _thesis, outline = self._start()
        service = self.env['irg.tfm.esquema'].with_user(user)
        short_question = outline.question_ids.filtered(
            lambda item: item.question_type == 'char_box'
            and not item.prefill_source
        )[:1]
        long_question = outline.question_ids.filtered(
            lambda item: item.question_type == 'text_box'
        )[:1]
        choice_question = outline.question_ids.filtered(
            lambda item: item.question_type == 'multiple_choice'
        )[:1]

        with self.assertRaisesRegex(ValidationError, '500 caracteres'):
            service._irg_portal_save_step(
                course.id, outline.id, short_question.step_key, outline.revision,
                {str(short_question.id): 'x' * 501},
            )
        with self.assertRaisesRegex(ValidationError, '20000 caracteres'):
            service._irg_portal_save_step(
                course.id, outline.id, long_question.step_key, outline.revision,
                {str(long_question.id): 'x' * 20001},
            )
        with self.assertRaisesRegex(ValidationError, 'demasiadas opciones'):
            service._irg_portal_save_step(
                course.id, outline.id, choice_question.step_key, outline.revision,
                {str(choice_question.id): list(range(1, 52))},
            )

        proposal_answers = {}
        for question in outline.question_ids.filtered(
            lambda item: item.step_key == 'proposal'
        ):
            if question.question_type == 'multiple_choice':
                proposal_answers[str(question.id)] = [question.option_ids[0].id]
            elif question.prefill_source == 'student_email':
                proposal_answers[str(question.id)] = 'student@example.test'
            else:
                proposal_answers[str(question.id)] = 'x' * 500
        outline = service._irg_portal_save_step(
            course.id, outline.id, 'proposal', outline.revision, proposal_answers,
        )
        approach_answers = {
            str(question.id): 'x' * 20000
            for question in outline.question_ids.filtered(
                lambda item: item.step_key == 'approach'
            )
        }
        outline = service._irg_portal_save_step(
            course.id, outline.id, 'approach', outline.revision, approach_answers,
        )
        results_answers = {
            str(question.id): 'x' * 20000
            for question in outline.question_ids.filtered(
                lambda item: item.step_key == 'results'
            )
        }
        with self.assertRaisesRegex(ValidationError, 'máximo total'):
            service._irg_portal_save_step(
                course.id, outline.id, 'results', outline.revision, results_answers,
            )

    def test_template_question_and_option_limits_are_enforced(self):
        last_page = self.env.ref('irg_tfm_convocatorias.tfm_outline_page_results')
        self.env['survey.question'].create([
            {
                'survey_id': self.survey.id,
                'title': 'Pregunta adicional %s' % index,
                'sequence': last_page.sequence + index + 1,
                'question_type': 'char_box',
            }
            for index in range(91)
        ])
        with self.assertRaisesRegex(ValidationError, '100 preguntas'):
            self.env['irg.tfm.esquema']._irg_template_snapshot(self.survey)

        self.env['survey.question'].search([
            ('survey_id', '=', self.survey.id),
            ('title', 'like', 'Pregunta adicional '),
        ]).unlink()
        modality = self.env.ref('irg_tfm_convocatorias.tfm_outline_modality')
        self.env['survey.question.answer'].create([
            {
                'question_id': modality.id,
                'value': 'Opción adicional %s' % index,
            }
            for index in range(97)
        ])
        with self.assertRaisesRegex(ValidationError, '100 opciones'):
            self.env['irg.tfm.esquema']._irg_template_snapshot(self.survey)

    def test_submit_versions_snapshot_and_never_creates_email_notifications(self):
        user, _student, course, _enrollment, thesis, outline = self._start()
        Outline = self.env['irg.tfm.esquema'].with_user(user)
        outline = self._fill_required(user, course, outline)
        mail_count = self.env['mail.mail'].search_count([])
        notification_count = self.env['mail.notification'].search_count([])
        done = Outline._irg_portal_submit(course.id, outline.id, outline.revision)
        self.assertEqual(done.state, 'done')
        self.assertEqual(done.version, 1)
        self.assertTrue(done.submitted_at)
        self.assertTrue(thesis._irg_has_tfm_outline_submission())
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count)
        self.assertEqual(
            self.env['mail.notification'].search_count([]), notification_count,
        )
        audit = self.env['mail.message'].search([
            ('model', '=', 'tesis.model'),
            ('res_id', '=', thesis.id),
            ('body', 'ilike', 'versión 1'),
        ])
        self.assertEqual(len(audit), 1)
        self.assertFalse(audit.partner_ids)
        self.assertFalse(audit.notification_ids)

        second = Outline._irg_portal_start(course.id)
        second = self._fill_required(user, course, second)
        second = Outline._irg_portal_submit(course.id, second.id, second.revision)
        self.assertEqual(second.version, 2)

    def test_convocation_blocks_start_save_and_submit_then_removal_reopens(self):
        user, _student, course, _enrollment, thesis, outline = self._start()
        convocation = self._convocation()
        thesis.write({'irg_tfm_convocation_id': convocation.id})
        Outline = self.env['irg.tfm.esquema'].with_user(user)
        with self.assertRaises(ValidationError):
            Outline._irg_portal_start(course.id)
        with self.assertRaises(ValidationError):
            Outline._irg_portal_save_step(
                course.id, outline.id, 'proposal', outline.revision, {},
            )
        with self.assertRaises(ValidationError):
            Outline._irg_portal_submit(course.id, outline.id, outline.revision)
        thesis.write({'irg_tfm_convocation_id': False})
        self.assertEqual(Outline._irg_portal_start(course.id), outline)

    def test_completed_outline_and_frozen_rows_are_immutable(self):
        user, _student, course, _enrollment, _thesis, outline = self._start()
        outline = self._fill_required(user, course, outline)
        done = self.env['irg.tfm.esquema'].with_user(user)._irg_portal_submit(
            course.id, outline.id, outline.revision,
        )
        with self.assertRaises(AccessError):
            done.sudo().write({'current_step': 'proposal'})
        with self.assertRaises(AccessError):
            done.sudo().unlink()
        with self.assertRaises(AccessError):
            done.sudo().copy()
        with self.assertRaises(AccessError):
            done.question_ids[0].sudo().write({'answer_text': 'changed'})

    def test_reviewer_group_reads_done_but_not_draft_and_cannot_mutate(self):
        _user, _student, _course, _enrollment, _thesis, outline = self._start()
        reviewer = self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'TFM reviewer',
            'login': 'reviewer.%s@example.test' % self._suffix(),
            'groups_id': [Command.set([
                self.env.ref('irg_tfm_convocatorias.group_tfm_reviewer').id,
            ])],
        })
        self.assertFalse(
            self.env['irg.tfm.esquema'].with_user(reviewer).search([
                ('id', '=', outline.id),
            ])
        )
        outline.sudo().with_context(_irg_tfm_outline_service=True).write({
            'state': 'done', 'version': 1,
            'submitted_at': outline.started_at,
        })
        visible = self.env['irg.tfm.esquema'].with_user(reviewer).search([
            ('id', '=', outline.id),
        ])
        self.assertEqual(visible, outline)
        with self.assertRaises(AccessError):
            visible.write({'current_step': 'proposal'})

    def test_template_and_portal_contract_do_not_create_native_survey_attempts(self):
        user, _student, _course, _enrollment, _thesis, _outline = self._start()
        self.assertFalse(self.env['survey.user_input'].search([
            ('survey_id', '=', self.survey.id),
        ]))
        with self.assertRaisesRegex(UserError, 'plantilla TFM'):
            self.survey.sudo()._create_answer(user=user)
        with self.assertRaisesRegex(UserError, 'plantillas TFM'):
            self.env['survey.user_input'].sudo().create({
                'survey_id': self.survey.id,
                'partner_id': user.partner_id.id,
            })
        self.assertFalse(self.env['survey.user_input'].search([
            ('survey_id', '=', self.survey.id),
        ]))


@tagged('post_install', '-at_install')
class TestTfmOutlineSurveyPortal(TfmFixtureMixin, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        helper = TfmFixtureMixin()
        helper.env = cls.env
        cls.owner, _student, cls.course, _enrollment, cls.thesis = helper._portal_case(
            login='tfm_outline_http_owner.%s@example.test' % helper._suffix(),
        )
        cls.outsider, _student, _course, _enrollment, _thesis = helper._portal_case(
            login='tfm_outline_http_outsider.%s@example.test' % helper._suffix(),
        )
        cls.survey = cls.env.ref('irg_tfm_convocatorias.tfm_outline_survey')

    def _csrf_from(self, response):
        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
        self.assertTrue(match, 'The rendered form must contain a CSRF token.')
        return match.group(1)

    def test_portal_renders_multiple_questions_and_secures_start_save_and_ids(self):
        self.authenticate(self.owner.login, self.owner.login)
        landing = self.url_open('/campus/course/%s/tfm' % self.course.id)
        self.assertIn('Comenzar cuestionario', landing.text)
        before = self.env['irg.tfm.esquema'].sudo().search_count([
            ('thesis_id', '=', self.thesis.id),
        ])
        rejected = self.url_open(
            '/campus/course/%s/tfm/outline/start' % self.course.id,
            data={},
            allow_redirects=False,
        )
        self.assertEqual(rejected.status_code, 400)
        self.assertEqual(
            self.env['irg.tfm.esquema'].sudo().search_count([
                ('thesis_id', '=', self.thesis.id),
            ]),
            before,
        )

        started = self.url_open(
            '/campus/course/%s/tfm/outline/start' % self.course.id,
            data={'csrf_token': self._csrf_from(landing)},
            allow_redirects=False,
        )
        self.assertIn(started.status_code, (302, 303))
        self.env.invalidate_all()
        outline = self.env['irg.tfm.esquema'].sudo().search([
            ('thesis_id', '=', self.thesis.id), ('state', '=', 'draft'),
        ], limit=1)
        self.assertTrue(outline)
        form = self.url_open(started.headers['Location'])
        proposal = outline.question_ids.filtered(
            lambda question: question.step_key == 'proposal'
        )
        self.assertGreater(len(proposal), 1)
        for question in proposal:
            self.assertIn(question.title, form.text)

        no_csrf = self.url_open(
            '/campus/course/%s/tfm/outline/%s/save' % (self.course.id, outline.id),
            data={'step': 'proposal', 'action': 'next', 'revision': outline.revision},
            allow_redirects=False,
        )
        self.assertEqual(no_csrf.status_code, 400)

        self.authenticate(self.outsider.login, self.outsider.login)
        foreign = self.url_open(
            '/campus/course/%s/tfm/outline/%s' % (self.course.id, outline.id),
            allow_redirects=False,
        )
        self.assertEqual(foreign.status_code, 404)

        self.authenticate(self.owner.login, self.owner.login)
        form = self.url_open(
            '/campus/course/%s/tfm/outline/%s' % (self.course.id, outline.id)
        )
        values = {
            'csrf_token': self._csrf_from(form),
            'step': 'proposal',
            'action': 'next',
            'revision': str(outline.revision),
        }
        for question in proposal:
            key = 'question_%s' % question.id
            if question.question_type in ('simple_choice', 'multiple_choice'):
                values[key] = str(question.option_ids[0].id)
            else:
                values[key] = question.answer_text or 'Respuesta editable'
        saved = self.url_open(
            '/campus/course/%s/tfm/outline/%s/save' % (self.course.id, outline.id),
            data=values,
            allow_redirects=False,
        )
        self.assertIn(saved.status_code, (302, 303))
        self.assertIn('step=approach', saved.headers['Location'])

        self.env.invalidate_all()
        outline = outline.exists()
        stale_form = self.url_open(
            '/campus/course/%s/tfm/outline/%s?step=proposal'
            % (self.course.id, outline.id)
        )
        stale = self.url_open(
            '/campus/course/%s/tfm/outline/%s/save' % (self.course.id, outline.id),
            data={
                'csrf_token': self._csrf_from(stale_form),
                'step': 'proposal',
                'action': 'save',
                'revision': '0',
            },
            allow_redirects=False,
        )
        self.assertEqual(stale.status_code, 200)
        self.assertIn('otra pestaña', stale.text)

        for step, action in (('approach', 'next'), ('results', 'review')):
            self.env.invalidate_all()
            outline = outline.exists()
            step_form = self.url_open(
                '/campus/course/%s/tfm/outline/%s?step=%s'
                % (self.course.id, outline.id, step)
            )
            step_values = {
                'csrf_token': self._csrf_from(step_form),
                'step': step,
                'action': action,
                'revision': str(outline.revision),
            }
            for question in outline.question_ids.filtered(
                lambda item: item.step_key == step
            ):
                key = 'question_%s' % question.id
                if question.question_type in ('simple_choice', 'multiple_choice'):
                    step_values[key] = str(question.option_ids[0].id)
                else:
                    step_values[key] = 'Respuesta HTTP de %s' % step
            step_saved = self.url_open(
                '/campus/course/%s/tfm/outline/%s/save'
                % (self.course.id, outline.id),
                data=step_values,
                allow_redirects=False,
            )
            self.assertIn(step_saved.status_code, (302, 303))

        review = self.url_open(step_saved.headers['Location'])
        self.assertIn('Revisar respuestas', review.text)
        self.assertIn('Enviar Esquema', review.text)
        self.env.invalidate_all()
        outline = outline.exists()
        submitted = self.url_open(
            '/campus/course/%s/tfm/outline/%s/submit'
            % (self.course.id, outline.id),
            data={
                'csrf_token': self._csrf_from(review),
                'revision': str(outline.revision),
            },
            allow_redirects=False,
        )
        self.assertIn(submitted.status_code, (302, 303))
        self.env.invalidate_all()
        done = self.env['irg.tfm.esquema'].sudo().search([
            ('thesis_id', '=', self.thesis.id), ('state', '=', 'done'),
        ], limit=1)
        self.assertEqual(done.version, 1)
        version_page = self.url_open(
            '/campus/course/%s/tfm/outline/%s' % (self.course.id, done.id)
        )
        self.assertEqual(version_page.status_code, 200)
        self.assertIn('Versión 1', version_page.text)
        self.assertIn('Respuesta HTTP de approach', version_page.text)

        landing = self.url_open('/campus/course/%s/tfm' % self.course.id)
        second_started = self.url_open(
            '/campus/course/%s/tfm/outline/start' % self.course.id,
            data={'csrf_token': self._csrf_from(landing)},
            allow_redirects=False,
        )
        self.assertIn(second_started.status_code, (302, 303))
        self.env.invalidate_all()
        draft = self.env['irg.tfm.esquema'].sudo().search([
            ('thesis_id', '=', self.thesis.id), ('state', '=', 'draft'),
        ], limit=1)
        self.assertTrue(draft)
        draft_form = self.url_open(second_started.headers['Location'])
        convocation = self._convocation()
        self.thesis.write({'irg_tfm_convocation_id': convocation.id})
        blocked = self.url_open(
            '/campus/course/%s/tfm/outline/%s/save' % (self.course.id, draft.id),
            data={
                'csrf_token': self._csrf_from(draft_form),
                'step': 'proposal',
                'action': 'save',
                'revision': str(draft.revision),
            },
            allow_redirects=False,
        )
        self.assertEqual(blocked.status_code, 200)
        self.assertIn('convocatoria asignada', blocked.text)

    def test_native_survey_url_cannot_create_an_attempt(self):
        self.authenticate(self.owner.login, self.owner.login)
        before = self.env['survey.user_input'].sudo().search_count([
            ('survey_id', '=', self.survey.id),
        ])
        self.survey.write({'access_mode': 'public'})
        try:
            response = self.url_open(
                '/survey/start/%s' % self.survey.access_token,
                allow_redirects=False,
            )
            self.assertIn(response.status_code, (302, 303))
        finally:
            self.survey.write({'access_mode': 'token'})
        self.assertEqual(
            self.env['survey.user_input'].sudo().search_count([
                ('survey_id', '=', self.survey.id),
            ]),
            before,
        )
