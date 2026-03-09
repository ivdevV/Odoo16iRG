import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    x_exam_auto_scale_100 = fields.Boolean(
        string='Auto escala 100',
        default=True,
        help='Si esta activo en examenes/certificaciones, distribuye puntos automaticamente para cerrar en 100.',
    )
    x_exam_target_score = fields.Float(
        string='Puntaje objetivo',
        default=100.0,
        help='Escala objetivo para el examen. Recomendado: 100.',
    )
    x_exam_equal_weight = fields.Boolean(
        string='Peso igual por pregunta',
        default=True,
        help='Si esta activo, cada pregunta puntuable vale target/N.',
    )
    x_exam_scored_question_count = fields.Integer(
        string='Preguntas puntuables',
        compute='_compute_exam_scale_stats',
    )
    x_exam_points_per_question = fields.Float(
        string='Puntos por pregunta',
        compute='_compute_exam_scale_stats',
        digits=(16, 4),
    )

    @api.depends('question_ids', 'question_ids.question_type', 'x_exam_target_score')
    def _compute_exam_scale_stats(self):
        for survey in self:
            questions = survey._get_scored_questions()
            count = len(questions)
            survey.x_exam_scored_question_count = count
            survey.x_exam_points_per_question = (survey.x_exam_target_score / count) if count else 0.0

    @api.constrains('x_exam_target_score', 'x_exam_auto_scale_100', 'survey_type')
    def _check_exam_scale_config(self):
        for survey in self:
            if not survey._is_exam_like() or not survey.x_exam_auto_scale_100:
                continue
            if survey.x_exam_target_score <= 0:
                raise ValidationError(_('El puntaje objetivo debe ser mayor que cero.'))

    def _is_exam_like(self):
        self.ensure_one()
        return self.survey_type in ('exam', 'cert')

    def _get_scored_questions(self):
        self.ensure_one()
        question_model_fields = self.env['survey.question']._fields
        questions = self.question_ids.filtered(lambda q: not getattr(q, 'is_page', False))

        if 'is_scored_question' in question_model_fields:
            questions = questions.filtered(lambda q: q.is_scored_question)

        # Excluye tipos no evaluables automaticamente.
        excluded_types = {'description_page', 'text_box', 'char_box', 'numerical_box', 'date', 'datetime', 'file'}
        if 'question_type' in question_model_fields:
            questions = questions.filtered(lambda q: q.question_type not in excluded_types)

        return questions

    def action_recalculate_exam_scale_100(self):
        self._recalculate_exam_scale_100(raise_if_empty=True)
        return True

    def _recalculate_exam_scale_100(self, raise_if_empty=False):
        answer_model_fields = self.env['survey.question.answer']._fields
        question_model_fields = self.env['survey.question']._fields

        for survey in self:
            if not survey._is_exam_like() or not survey.x_exam_auto_scale_100 or not survey.x_exam_equal_weight:
                continue

            questions = survey._get_scored_questions()
            count = len(questions)
            if not count:
                if raise_if_empty:
                    raise ValidationError(_('No hay preguntas puntuables para distribuir la escala a 100.'))
                continue

            target = survey.x_exam_target_score or 100.0
            base_points = round(target / count, 4)
            distributed = round(base_points * count, 4)
            residual = round(target - distributed, 4)

            # Cierra el redondeo en la ultima pregunta para garantizar suma exacta.
            point_map = [base_points] * count
            point_map[-1] = round(point_map[-1] + residual, 4)

            for question, question_points in zip(questions, point_map):
                answer_ids = question.suggested_answer_ids

                if answer_ids and 'answer_score' in answer_model_fields:
                    correct_answers = answer_ids.filtered(lambda ans: getattr(ans, 'is_correct', False))
                    answer_ids.with_context(no_exam_scale_recompute=True).write({'answer_score': 0.0})

                    if correct_answers:
                        per_answer = round(question_points / len(correct_answers), 4)
                        correction = round(question_points - (per_answer * len(correct_answers)), 4)
                        score_map = [per_answer] * len(correct_answers)
                        score_map[-1] = round(score_map[-1] + correction, 4)

                        for answer, answer_score in zip(correct_answers, score_map):
                            answer.with_context(no_exam_scale_recompute=True).write({'answer_score': answer_score})

                if 'answer_score' in question_model_fields:
                    question.with_context(no_exam_scale_recompute=True).write({'answer_score': question_points})

            _logger.info(
                'Exam scale recalculated to %s for survey %s with %s questions',
                target,
                survey.id,
                count,
            )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._recalculate_exam_scale_100(raise_if_empty=False)
        return records

    def write(self, vals):
        res = super().write(vals)
        trigger_keys = {'survey_type', 'x_exam_auto_scale_100', 'x_exam_target_score', 'x_exam_equal_weight'}
        if trigger_keys.intersection(vals.keys()):
            self._recalculate_exam_scale_100(raise_if_empty=False)
        return res
