# -*- coding: utf-8 -*-
from odoo import fields, models


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    # Enlace propio al survey. No se usa slide.slide.survey_id ni se cambia
    # slide_category: isep_slide_article_custom solo pega el HTML en pantalla
    # completa cuando la categoría sigue siendo article.
    oral_case_enabled = fields.Boolean(
        string='Caso oral',
        default=False,
        help='Activa la entrega de la grabación de este artículo a n8n.',
    )
    oral_case_code = fields.Char(
        string='Código del caso',
        help='Identificador que se envía a n8n, por ejemplo DA-ORAL-001.',
    )
    oral_case_survey_id = fields.Many2one(
        'survey.survey',
        string='Encuesta del caso oral',
        help='Participación que n8n debe actualizar con la sugerencia de la IA.',
    )
