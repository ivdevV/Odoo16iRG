# -*- coding: utf-8 -*-

from odoo import _, api, models
from odoo.exceptions import ValidationError


class PracticeRequest(models.Model):
    _inherit = 'practice.request'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._irg_check_portal_practice_eligibility()
        return records

    def write(self, vals):
        result = super().write(vals)
        if any(key in vals for key in ('course_id', 'op_admission_id')):
            self._irg_check_portal_practice_eligibility()
        return result

    def _irg_check_portal_practice_eligibility(self):
        if not self.env.user.has_group('base.group_portal'):
            return
        for record in self:
            record._irg_raise_if_practice_ineligible()

    def _irg_raise_if_practice_ineligible(self):
        self.ensure_one()
        enrollment = self.course_id
        if (
            not enrollment
            or not enrollment.student_id
            or enrollment.student_id.user_id != self.env.user
        ):
            raise ValidationError(_(
                'No puedes solicitar prácticas para una matrícula que no es tuya.'
            ))
        admission = self.op_admission_id
        if admission and admission.student_id != enrollment.student_id:
            raise ValidationError(_(
                'La admisión no corresponde al alumno de la matrícula.'
            ))
        reason = (
            enrollment.irg_practice_request_block_reason()
            if enrollment else 'completion'
        )
        if reason == 'diplomado' or (
            admission
            and admission.course_id
            and admission.course_id.irg_excludes_practice_request()
        ):
            raise ValidationError(_(
                'Los diplomados no incluyen solicitud de prácticas.'
            ))
        if reason:
            raise ValidationError(_(
                'Puedes solicitar prácticas cuando el avance del curso '
                'llegue al 50% de las asignaturas obligatorias.'
            ))
        if (
            admission
            and admission.course_id
            and enrollment
            and admission.course_id != enrollment.course_id
        ):
            raise ValidationError(_(
                'La matrícula no corresponde al curso seleccionado.'
            ))
