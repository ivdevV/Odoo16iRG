# -*- coding: utf-8 -*-

from odoo import api, models

IRG_PRACTICE_COMPLETION_MINIMUM = 50.0


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
