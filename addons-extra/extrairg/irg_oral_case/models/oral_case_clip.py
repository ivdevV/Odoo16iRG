# -*- coding: utf-8 -*-
import math

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

AI_FIELDS = {'score_ia', 'resumen_ia'}


class IrgOralCaseClip(models.Model):
    _name = 'irg.oral.case.clip'
    _description = 'Intervención grabada de un tramo'
    _order = 'segment_index, id'

    job_id = fields.Many2one(
        'irg.oral.case.job',
        string='Entrega',
        required=True,
        ondelete='cascade',
        index=True,
    )
    segment_id = fields.Many2one(
        'irg.oral.case.segment',
        string='Tramo',
        ondelete='restrict',
    )
    segment_index = fields.Integer(string='Índice del tramo', required=True)
    prompt_snapshot = fields.Text(string='Consigna para la IA')
    student_text_snapshot = fields.Text(string='Texto que vio la alumna')
    clip_url_snapshot = fields.Char(string='Clip de la paciente')
    duration_seconds = fields.Float(string='Duración (segundos)')
    video_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Grabación',
        ondelete='set null',
        copy=False,
    )
    score_ia = fields.Float(
        string='Nota propuesta por IA',
        help='Sugerencia de la IA para este tramo. No es la nota del cuaderno.',
    )
    resumen_ia = fields.Text(
        string='Resumen propuesto por IA',
        help='Comentario de la IA sobre este tramo. No es la nota del cuaderno.',
    )

    def _can_write_ai(self):
        user = self.env.user
        return bool(
            self.env.su
            or user.has_group('base.group_system')
            or user.has_group('openeducat_core.group_op_faculty')
            or user.has_group('irg_oral_case.group_oral_case_teacher')
        )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            raise AccessError(_('Solo el sistema puede registrar la intervención.'))
        return super().create(vals_list)

    def write(self, vals):
        vals = dict(vals)
        if self.env.su:
            self._check_ai_values(vals)
            return super().write(vals)
        extra = set(vals) - AI_FIELDS
        if extra or not vals or not self._can_write_ai():
            raise AccessError(_('No se puede reasignar la intervención ni su grabación.'))
        self._check_ai_values(vals)
        return super().write(vals)

    def unlink(self):
        if not self.env.su:
            raise AccessError(_('Solo el sistema puede borrar la intervención.'))
        return super().unlink()

    def _check_ai_values(self, vals):
        if 'score_ia' in vals and vals['score_ia'] not in (None, False):
            score = vals['score_ia']
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score):
                raise ValidationError(_('La nota propuesta del tramo tiene que ser un número.'))
            if score < 0 or score > 10:
                raise ValidationError(_('La nota propuesta del tramo tiene que estar entre 0 y 10.'))
        if isinstance(vals.get('resumen_ia'), str) and len(vals['resumen_ia']) > 8000:
            vals['resumen_ia'] = vals['resumen_ia'][:8000]

    @api.constrains('score_ia')
    def _check_score_ia(self):
        for clip in self:
            if clip.score_ia in (None, False):
                continue
            if not math.isfinite(clip.score_ia) or clip.score_ia < 0 or clip.score_ia > 10:
                raise ValidationError(_('La nota propuesta del tramo tiene que estar entre 0 y 10.'))
