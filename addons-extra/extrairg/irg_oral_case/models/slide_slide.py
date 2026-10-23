# -*- coding: utf-8 -*-
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .oral_case_segment import MAX_SEGMENTS, clean_https_url


class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    # Enlace propio al survey. No se usa slide.slide.survey_id ni se cambia
    # slide_category: el artículo sigue pegándose en pantalla completa.
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
    oral_case_mode = fields.Selection(
        [
            ('single', 'Un solo vídeo'),
            ('clips', 'Caso por clips'),
        ],
        string='Modo del caso',
        default='single',
        required=True,
        help='Un solo vídeo conserva la entrega actual. Por clips, la alumna interviene después de cada tramo.',
    )
    oral_case_keep_video = fields.Boolean(
        string='Conservar las grabaciones en Odoo',
        default=False,
        help='Si está activo, el profesor puede ver las grabaciones de este caso. '
             'Si no, no se guarda copia. La decisión de política sigue pendiente.',
    )
    oral_case_listen_clip_url = fields.Char(
        string='Clip de escucha del caso',
        help='Opcional. Se usa en los tramos que no tienen el suyo. https, en bucle y en silencio.',
    )
    oral_case_segment_ids = fields.One2many(
        'irg.oral.case.segment',
        'slide_id',
        string='Tramos',
    )

    @api.constrains('oral_case_listen_clip_url')
    def _check_oral_listen_url(self):
        for slide in self:
            if slide.oral_case_listen_clip_url:
                clean_https_url(slide.oral_case_listen_clip_url, required=True)

    def _irg_check_oral_segment_count(self):
        segment_model = self.env['irg.oral.case.segment']
        for slide in self:
            count = segment_model.search_count([('slide_id', '=', slide.id)])
            if count > MAX_SEGMENTS:
                raise ValidationError(_(
                    'Un caso admite como máximo %s tramos.'
                ) % MAX_SEGMENTS)

    def write(self, vals):
        if 'oral_case_listen_clip_url' in vals and vals.get('oral_case_listen_clip_url'):
            vals = dict(vals)
            vals['oral_case_listen_clip_url'] = clean_https_url(
                vals.get('oral_case_listen_clip_url'), required=True,
            )
        return super().write(vals)
