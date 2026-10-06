# -*- coding: utf-8 -*-

from odoo import models


class OpStudent(models.Model):
    _inherit = 'op.student'

    def irg_can_request_any_practice(self):
        if len(self) != 1:
            return False
        enrollments = self.env['op.student.course'].sudo().search([
            ('student_id', '=', self.id),
        ])
        return any(
            enrollment.irg_can_request_practice() for enrollment in enrollments
        )
