# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PracticeRequest(models.Model):
    _inherit = 'practice.request'

    irg_practice_part = fields.Selection(
        selection=[
            ('1', 'Parte 1'),
            ('2', 'Parte 2'),
        ],
        string='Parte de las prácticas',
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._irg_check_portal_practice_eligibility()
        return records

    def write(self, vals):
        result = super().write(vals)
        if any(key in vals for key in (
            'course_id', 'op_admission_id', 'country_id', 'state_id',
            'irg_practice_part',
        )):
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
            raise ValidationError(enrollment.irg_practice_locked_message())
        part_error = enrollment.irg_practice_part_error(self.irg_practice_part)
        if part_error:
            raise ValidationError(part_error)
        if (
            admission
            and admission.course_id
            and enrollment
            and admission.course_id != enrollment.course_id
        ):
            raise ValidationError(_(
                'La matrícula no corresponde al curso seleccionado.'
            ))
        location_error = self._irg_practice_location_error()
        if location_error:
            raise ValidationError(location_error)

    def _irg_practice_location_error(self):
        self.ensure_one()
        if not self.country_id:
            return _(
                'Selecciona el país en donde realizaras las prácticas.'
            )
        if not self.state_id or self.state_id.country_id != self.country_id:
            return _(
                'Selecciona la ciudad en donde realizaras las prácticas.'
            )
        return False

    def irg_blocking_same_part(self, part):
        """Requests that already occupy the part being submitted.

        Other courses allow a single request. NC allows one request per part,
        so part 1 does not block part 2.
        """
        if not self:
            return self
        course = self[:1].course_id.course_id
        if not course or not course.irg_is_nc_practice_course():
            return self[:1]
        if str(part or '') not in ('1', '2'):
            return self[:1]
        return self.filtered(
            lambda request: request.irg_practice_part == str(part)
        )[:1]
