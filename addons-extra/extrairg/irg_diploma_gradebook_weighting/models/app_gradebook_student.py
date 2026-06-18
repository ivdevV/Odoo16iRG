# -*- coding: utf-8 -*-
import re
import unicodedata

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    diploma_recovery_required = fields.Boolean(
        string='Requiere recuperación diplomado',
        compute='_compute_diploma_recovery_required',
        store=True,
        readonly=True,
    )
    diploma_recovery_score = fields.Float(
        string='Nota recuperación diplomado',
        tracking=True,
    )
    diploma_recovery_applied = fields.Boolean(
        string='Recuperación diplomado aplicada',
        compute='_compute_diploma_recovery_applied',
        store=True,
        readonly=True,
    )

    @api.depends(
        'course_id.course_type_id.name',
        'course_id.course_type_id.code',
        'gradebook_subject_ids.final_subject_note',
        'gradebook_subject_ids.op_subject_id.name',
        'gradebook_subject_ids.op_subject_id.subject_type',
    )
    def _compute_diploma_recovery_required(self):
        for rec in self:
            values = rec._get_diploma_weighting_values()
            rec.diploma_recovery_required = bool(
                values and values['base_final'] < 7.0
            )

    @api.depends('diploma_recovery_required', 'diploma_recovery_score')
    def _compute_diploma_recovery_applied(self):
        for rec in self:
            rec.diploma_recovery_applied = (
                rec.diploma_recovery_required
                and rec.diploma_recovery_score > 0.0
            )

    @api.constrains('diploma_recovery_score')
    def _check_diploma_recovery_score(self):
        for rec in self:
            if rec.diploma_recovery_score < 0.0:
                raise ValidationError(_(
                    'La nota de recuperación del diplomado no puede ser negativa.'
                ))
            if rec.diploma_recovery_score > 7.0:
                raise ValidationError(_(
                    'La nota de recuperación del diplomado no puede ser mayor a 7.'
                ))

    @api.depends(
        'course_id.course_type_id.name',
        'course_id.course_type_id.code',
        'gradebook_subject_ids.final_subject_note',
        'gradebook_subject_ids.op_subject_id.name',
        'gradebook_subject_ids.op_subject_id.subject_type',
        'diploma_recovery_required',
        'diploma_recovery_score',
        'diploma_recovery_applied',
    )
    def _amount_prod_final(self):
        super()._amount_prod_final()
        for rec in self:
            diploma_final = rec._get_diploma_final_score()
            if diploma_final is not False:
                rec.total_final = diploma_final

    @api.depends(
        'student_id',
        'gradebook_subject_ids',
        'gradebook_subject_ids.final_subject_note',
        'gradebook_subject_ids.op_subject_id',
        'gradebook_subject_ids.op_subject_id.name',
        'gradebook_subject_ids.op_subject_id.subject_type',
        'course_id.course_type_id.name',
        'course_id.course_type_id.code',
        'diploma_recovery_required',
        'diploma_recovery_score',
        'diploma_recovery_applied',
    )
    def compute_avg_score(self):
        super().compute_avg_score()
        for rec in self:
            diploma_final = rec._get_diploma_final_score()
            if diploma_final is not False:
                rec.avg_score = diploma_final

    def _get_diploma_final_score(self):
        self.ensure_one()
        values = self._get_diploma_weighting_values()
        if not values:
            return False
        if self.diploma_recovery_applied:
            return min(self.diploma_recovery_score, 7.0)
        return values['base_final']

    def _get_diploma_weighting_values(self):
        self.ensure_one()
        if not self._is_diplomado_course():
            return False

        compulsory_subjects = self.gradebook_subject_ids.filtered(
            lambda line: line.op_subject_id.subject_type == 'compulsory'
        )
        presencial_subjects = compulsory_subjects.filtered(
            lambda line: self._is_presential_module_subject(line)
        )
        if not presencial_subjects:
            return False

        non_presential_subjects = compulsory_subjects - presencial_subjects
        if not non_presential_subjects:
            return False

        presencial_score = presencial_subjects[0].final_subject_note
        non_presential_average = (
            sum(non_presential_subjects.mapped('final_subject_note'))
            / len(non_presential_subjects)
        )
        base_final = (presencial_score * 0.5) + (non_presential_average * 0.5)
        return {
            'base_final': base_final,
            'presencial_score': presencial_score,
            'non_presential_average': non_presential_average,
        }

    def _is_diplomado_course(self):
        self.ensure_one()
        course_type = self.course_id.course_type_id
        if not course_type:
            return False

        normalized_name = self._normalize_text(course_type.name)
        normalized_code = self._normalize_text(course_type.code)
        return (
            normalized_name in ('diplomado', 'diplomados')
            or normalized_name.startswith('diplomado ')
            or normalized_code.startswith('dip')
        )

    def _is_presential_module_subject(self, gradebook_subject):
        subject_name = gradebook_subject.op_subject_id.name or gradebook_subject.name
        return self._normalize_text(subject_name) == 'modulo presencial'

    @api.model
    def _normalize_text(self, value):
        if not value:
            return ''
        normalized = unicodedata.normalize('NFKD', value)
        normalized = normalized.encode('ascii', 'ignore').decode('ascii')
        normalized = normalized.lower()
        return re.sub(r'\s+', ' ', normalized).strip()
