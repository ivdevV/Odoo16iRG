# -*- coding: utf-8 -*-

from odoo import models


class OpStudent(models.Model):
    _inherit = 'op.student'

    def irg_get_practice_center_type(self, course):
        """Return the practice modality of this student for a given course."""
        self.ensure_one()
        if not course:
            return self.env['practice.center.type']
        enrollment = self.course_detail_ids.filtered(
            lambda rec: rec.course_id.id == course.id
        )[:1]
        return enrollment.irg_practice_center_type_id
