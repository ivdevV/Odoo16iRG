from odoo import fields, models


class SurveyQuestion(models.Model):
    _inherit = 'survey.question'

    x_feedback_generic = fields.Text(
        string='Feedback generico',
        help='Retroalimentacion general de la pregunta importada desde TXT.',
    )
