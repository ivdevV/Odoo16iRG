from odoo import api, models


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('no_exam_scale_recompute'):
            records.mapped('survey_id')._recalculate_exam_scale_100(raise_if_empty=False)
        return records

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('no_exam_scale_recompute'):
            self.mapped('survey_id')._recalculate_exam_scale_100(raise_if_empty=False)
        return res

    def unlink(self):
        surveys = self.mapped('survey_id')
        res = super().unlink()
        if not self.env.context.get('no_exam_scale_recompute'):
            surveys._recalculate_exam_scale_100(raise_if_empty=False)
        return res


class SurveyQuestionAnswer(models.Model):
    _inherit = 'survey.question.answer'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('no_exam_scale_recompute'):
            records.mapped('question_id.survey_id')._recalculate_exam_scale_100(raise_if_empty=False)
        return records

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('no_exam_scale_recompute'):
            self.mapped('question_id.survey_id')._recalculate_exam_scale_100(raise_if_empty=False)
        return res

    def unlink(self):
        surveys = self.mapped('question_id.survey_id')
        res = super().unlink()
        if not self.env.context.get('no_exam_scale_recompute'):
            surveys._recalculate_exam_scale_100(raise_if_empty=False)
        return res
