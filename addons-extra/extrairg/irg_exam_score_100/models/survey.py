# -*- coding: utf-8 -*-
from odoo import models, fields


class SurveySurvey(models.Model):
    _inherit = 'survey.survey'

    x_exam_auto_scale_100 = fields.Boolean(string='Exam auto scale 100', default=False)
