from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


_TFM_STEP_SELECTION = [
    ('proposal', 'Datos y propuesta'),
    ('approach', 'Planteamiento'),
    ('results', 'Resultados y fuentes'),
]


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    irg_tfm_step_key = fields.Selection(
        _TFM_STEP_SELECTION,
        string='Paso técnico TFM',
        help='Identidad estable del paso. El título visible de la sección puede cambiar.',
    )
    irg_tfm_prefill_source = fields.Selection(
        [
            ('student_name', 'Nombre del alumno'),
            ('student_email', 'Correo del alumno'),
            ('master_name', 'Máster de la matrícula'),
        ],
        string='Dato automático TFM',
    )

    @api.constrains(
        'is_page', 'question_type', 'irg_tfm_step_key', 'irg_tfm_prefill_source',
    )
    def _check_tfm_question_metadata(self):
        for question in self:
            if question.irg_tfm_step_key and not question.is_page:
                raise ValidationError(_('A TFM step key can only be set on a survey section.'))
            if question.irg_tfm_prefill_source and question.is_page:
                raise ValidationError(_('A TFM automatic value can only be set on a question.'))
            if (
                question.irg_tfm_prefill_source
                and question.question_type != 'char_box'
            ):
                raise ValidationError(_(
                    'A TFM automatic value requires a short-text question.'
                ))
