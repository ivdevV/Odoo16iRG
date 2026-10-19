# -*- coding: utf-8 -*-

from odoo import api, models

IRG_PRACTICE_COMPLETION_MINIMUM = 60.0
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


class OpStudentCourse(models.Model):
    _inherit = 'op.student.course'

    def _irg_practice_completion_percentage(self):
        """Read completion_porc without trusting a stale cache."""
        self.ensure_one()
        enrollment = self.sudo()
        enrollment.invalidate_recordset(['completion_porc'])
        return float(enrollment.completion_porc or 0.0)

    def irg_practice_request_block_reason(self):
        """Return why this enrollment cannot request practices, or False."""
        self.ensure_one()
        course = self.course_id
        if not course or course.irg_excludes_practice_request():
            return 'diplomado'
        if self._irg_practice_completion_percentage() < IRG_PRACTICE_COMPLETION_MINIMUM:
            return 'completion'
        return False

    def irg_can_request_practice(self):
        self.ensure_one()
        return not self.irg_practice_request_block_reason()

    @api.model
    def irg_practice_locked_message(self):
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
