from odoo import api, models


EXAM_ATTEMPTS_LIMIT = 2


class SurveySurveySecondAttemptFix(models.Model):
    _inherit = 'survey.survey'

    def _irg_prepare_exam_second_attempt_values(self, values):
        prepared_values = dict(values)
        if (
            'attempts_limit' in self._fields
            and prepared_values.get('survey_type') == 'exam'
        ):
            prepared_values['is_attempts_limited'] = True
            if prepared_values.get('attempts_limit', 0) < EXAM_ATTEMPTS_LIMIT:
                prepared_values['attempts_limit'] = EXAM_ATTEMPTS_LIMIT
        return prepared_values

    @api.model
    def create(self, values):
        values = self._irg_prepare_exam_second_attempt_values(values)
        return super().create(values)

    def write(self, values):
        if 'attempts_limit' not in self._fields:
            return super().write(values)

        target_type = values.get('survey_type')
        exam_surveys = self.filtered(
            lambda survey: (target_type or survey.survey_type) == 'exam'
        )
        other_surveys = self - exam_surveys

        result = True
        if other_surveys:
            result = super(SurveySurveySecondAttemptFix, other_surveys).write(
                dict(values)
            ) and result
        if exam_surveys:
            exam_values = dict(values)
            exam_values['is_attempts_limited'] = True
            if exam_values.get('attempts_limit', 0) < EXAM_ATTEMPTS_LIMIT:
                exam_values['attempts_limit'] = EXAM_ATTEMPTS_LIMIT
            result = super(SurveySurveySecondAttemptFix, exam_surveys).write(
                exam_values
            ) and result

        return result

    @api.model
    def irg_fix_exam_attempt_limits(self):
        if 'attempts_limit' not in self._fields:
            return True

        exam_surveys = self.sudo().search([
            ('survey_type', '=', 'exam'),
            '|',
            ('is_attempts_limited', '=', False),
            ('attempts_limit', '<', EXAM_ATTEMPTS_LIMIT),
        ])
        if exam_surveys:
            exam_surveys.write({
                'is_attempts_limited': True,
                'attempts_limit': EXAM_ATTEMPTS_LIMIT,
            })
        return True
