# -*- coding: utf-8 -*-
from urllib.parse import urlsplit

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

MAX_SEGMENTS = 20
MAX_SEGMENT_SECONDS = 14400


def clean_https_url(value, required=False):
    """Devuelve la URL si es https sin userinfo, espacios ni barra invertida."""
    if value in (None, False, ''):
        if required:
            raise ValidationError(_('El tramo necesita una URL https.'))
        return False
    if not isinstance(value, str):
        raise ValidationError(_('La URL del tramo tiene que ser texto https.'))
    text = value.strip()
    if text != value or any(char in text for char in (' ', '\\', '\n', '\r', '\t')):
        raise ValidationError(_('La URL del tramo no puede llevar espacios ni barra invertida.'))
    parts = urlsplit(text)
    if parts.scheme != 'https' or parts.username or parts.password or not parts.hostname:
        raise ValidationError(_('La URL del tramo tiene que ser https, sin usuario ni contraseña.'))
    return text


class IrgOralCaseSegment(models.Model):
    _name = 'irg.oral.case.segment'
    _description = 'Tramo de un caso clínico'
    _order = 'sequence, id'

    slide_id = fields.Many2one(
        'slide.slide',
        string='Slide',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(string='Orden', default=10)
    name = fields.Char(string='Nombre', required=True)
    clip_url = fields.Char(
        string='URL del clip',
        required=True,
        help='Vídeo de la paciente: MP4 por https o URL de Vimeo.',
    )
    student_quote = fields.Char(
        string='Frase del tramo',
        help='Opcional. La alumna la ve como cita. Si está vacía, el widget no inventa una frase.',
    )
    student_text = fields.Text(
        string='Texto para la alumna',
        help='Consigna que ve la alumna. Si está vacío, ve la consigna para la IA.',
    )
    transcript = fields.Text(
        string='Transcripción',
        help='Opcional. La alumna puede leerla si no oye el vídeo. No se envía a n8n.',
    )
    prompt = fields.Text(
        string='Consigna para la IA',
        required=True,
        help='Es el campo prompt del contrato con n8n. No se muestra a la alumna si hay texto para la alumna.',
    )
    max_seconds = fields.Integer(
        string='Tiempo máximo (segundos)',
        required=True,
        default=90,
    )
    allow_retry = fields.Boolean(
        string='Se puede repetir la toma',
        default=True,
        help='La alumna puede volver a grabar este tramo antes de enviar. El servidor recibe la toma final.',
    )
    listen_clip_url = fields.Char(
        string='Clip de escucha',
        help='Opcional. Se reproduce en bucle y en silencio mientras la alumna responde.',
    )

    def _check_slide_editor(self, slide):
        if self.env.su:
            return
        if not slide or not slide.exists():
            raise AccessError(_('El tramo tiene que pertenecer a un slide.'))
        slide.check_access_rights('write')
        slide.check_access_rule('write')

    @api.model_create_multi
    def create(self, vals_list):
        cleaned = []
        for vals in vals_list:
            vals = dict(vals)
            slide = self.env['slide.slide'].browse(vals.get('slide_id'))
            self._check_slide_editor(slide)
            vals['clip_url'] = clean_https_url(vals.get('clip_url'), required=True)
            if vals.get('listen_clip_url'):
                vals['listen_clip_url'] = clean_https_url(vals.get('listen_clip_url'))
            cleaned.append(vals)
        records = super().create(cleaned)
        records.mapped('slide_id')._irg_check_oral_segment_count()
        return records

    def write(self, vals):
        vals = dict(vals)
        if 'slide_id' in vals and not self.env.su:
            raise AccessError(_('No se puede mover un tramo a otro slide.'))
        if not self.env.su:
            for segment in self:
                segment._check_slide_editor(segment.slide_id)
        if 'clip_url' in vals:
            vals['clip_url'] = clean_https_url(vals.get('clip_url'), required=True)
        if vals.get('listen_clip_url'):
            vals['listen_clip_url'] = clean_https_url(vals.get('listen_clip_url'))
        elif 'listen_clip_url' in vals:
            vals['listen_clip_url'] = False
        result = super().write(vals)
        self.mapped('slide_id')._irg_check_oral_segment_count()
        return result

    def unlink(self):
        if not self.env.su:
            for segment in self:
                segment._check_slide_editor(segment.slide_id)
        return super().unlink()

    @api.constrains('max_seconds')
    def _check_max_seconds(self):
        for segment in self:
            if segment.max_seconds < 1 or segment.max_seconds > MAX_SEGMENT_SECONDS:
                raise ValidationError(_(
                    'El tiempo máximo del tramo tiene que estar entre 1 y %s segundos.'
                ) % MAX_SEGMENT_SECONDS)
