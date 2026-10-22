# -*- coding: utf-8 -*-

from odoo import _, api, models

IRG_PRACTICE_COMPLETION_MINIMUM = 60.0
IRG_NC_PRACTICE_PART1_MINIMUM = 25.0
IRG_PRACTICE_LOCKED_PARAGRAPHS = (
    'Para poder acceder al formulario de prácticas, el alumnado deberá haber '
    'completado previamente, como mínimo, el 60% de los módulos correspondientes '
    'al programa formativo, porcentaje que equivale aproximadamente a 6 exámenes '
    'superados.',
    'Hasta que no se alcance este requisito académico, el formulario de prácticas '
    'permanecerá inhabilitado.',
    'Una vez cumplido dicho porcentaje, el alumnado podrá acceder al formulario '
    'e iniciar el procedimiento de solicitud y gestión de las prácticas.',
)
IRG_NC_PRACTICE_LOCKED_PARAGRAPHS = (
    'Para poder solicitar las prácticas de la parte 1, el alumnado deberá '
    'haber completado previamente, como mínimo, el 25% de los módulos '
    'correspondientes al programa formativo.',
    'Hasta que no se alcance este requisito académico, el formulario de '
    'prácticas permanecerá inhabilitado.',
    'Las prácticas de la parte 2 se habilitan al completar el 60% de los '
    'módulos. Una vez cumplido el porcentaje que corresponda, el alumnado '
    'podrá acceder al formulario e iniciar la solicitud.',
)


class OpStudentCourse(models.Model):
    _inherit = 'op.student.course'

    def _irg_practice_completion_percentage(self):
        """Read completion_porc without trusting a stale cache."""
        self.ensure_one()
        enrollment = self.sudo()
        enrollment.invalidate_recordset(['completion_porc'])
        return float(enrollment.completion_porc or 0.0)

    def _irg_practice_minimum(self, part=None):
        """NC part 1 opens at 25%. Part 2 and every other course stay at 60%."""
        self.ensure_one()
        course = self.course_id
        if (
            course
            and course.irg_is_nc_practice_course()
            and str(part or '1') == '1'
        ):
            return IRG_NC_PRACTICE_PART1_MINIMUM
        return IRG_PRACTICE_COMPLETION_MINIMUM

    def irg_practice_request_block_reason(self, part=None):
        """Return why this enrollment cannot request practices, or False.

        Without a part, NC uses the part-1 threshold so the form opens at 25%.
        """
        self.ensure_one()
        course = self.course_id
        if not course or course.irg_excludes_practice_request():
            return 'diplomado'
        if self._irg_practice_completion_percentage() < self._irg_practice_minimum(part):
            return 'completion'
        return False

    def irg_practice_part_error(self, part):
        """NC must name the part. Part 2 stays locked until 60%."""
        self.ensure_one()
        course = self.course_id
        if not course or not course.irg_is_nc_practice_course():
            return False
        if str(part or '') not in ('1', '2'):
            return _(
                'Selecciona si las prácticas son de la parte 1 o de la parte 2.'
            )
        if self.irg_practice_request_block_reason(part) == 'completion':
            if str(part) == '2':
                return _(
                    'Las prácticas parte 2 se habilitan al completar '
                    'el 60% de los módulos.'
                )
            return self.irg_practice_locked_message()
        return False

    def irg_can_request_practice(self):
        self.ensure_one()
        return not self.irg_practice_request_block_reason()

    def irg_can_request_practice_part(self, part):
        self.ensure_one()
        if self.irg_practice_request_block_reason(part):
            return False
        return not self.irg_practice_part_error(part)

    def irg_practice_locked_message(self):
        if (
            len(self) == 1
            and self.course_id
            and self.course_id.irg_is_nc_practice_course()
        ):
            return '\n'.join(IRG_NC_PRACTICE_LOCKED_PARAGRAPHS)
        return '\n'.join(IRG_PRACTICE_LOCKED_PARAGRAPHS)

    @api.model
    def irg_portal_practice_allowed_for_course(self, course, partner):
        if not course or not partner:
            return False
        enrollments = self.sudo().search([
            ('course_id', '=', course.id),
            ('student_id.partner_id', '=', partner.id),
        ])
        return any(
            enrollment.irg_can_request_practice() for enrollment in enrollments
        )
