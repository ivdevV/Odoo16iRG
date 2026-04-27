from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSurveySecondAttempt(TransactionCase):
    def test_exam_create_sets_two_attempts(self):
        survey = self.env['survey.survey'].create({
            'title': 'Exam Second Attempt Test',
            'survey_type': 'exam',
        })

        self.assertTrue(survey.is_attempts_limited)
        self.assertEqual(survey.attempts_limit, 2)

    def test_exam_write_sets_two_attempts(self):
        survey = self.env['survey.survey'].create({
            'title': 'Survey Converted To Exam Test',
            'survey_type': 'survey',
        })

        survey.write({'survey_type': 'exam'})

        self.assertTrue(survey.is_attempts_limited)
        self.assertEqual(survey.attempts_limit, 2)

    def test_exam_keeps_higher_attempt_limit(self):
        survey = self.env['survey.survey'].create({
            'title': 'Exam Three Attempts Test',
            'survey_type': 'exam',
            'attempts_limit': 3,
        })

        self.assertTrue(survey.is_attempts_limited)
        self.assertEqual(survey.attempts_limit, 3)

    def test_fix_existing_exam_attempt_limits(self):
        survey = self.env['survey.survey'].create({
            'title': 'Existing Exam Limit Test',
            'survey_type': 'exam',
            'attempts_limit': 2,
        })
        survey._write({
            'is_attempts_limited': False,
            'attempts_limit': 1,
        })

        self.env['survey.survey'].irg_fix_exam_attempt_limits()
        survey.invalidate_cache(['is_attempts_limited', 'attempts_limit'])

        self.assertTrue(survey.is_attempts_limited)
        self.assertEqual(survey.attempts_limit, 2)
