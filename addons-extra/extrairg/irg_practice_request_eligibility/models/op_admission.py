# -*- coding: utf-8 -*-

from odoo import models


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    def irg_can_request_practice(self):
        self.ensure_one()
        if not self.student_id or not self.course_id:
            return False
        enrollments = self.env['op.student.course'].sudo().search([
            ('student_id', '=', self.student_id.id),
            ('course_id', '=', self.course_id.id),
        ])
        return any(
            enrollment.irg_can_request_practice() for enrollment in enrollments
        )
