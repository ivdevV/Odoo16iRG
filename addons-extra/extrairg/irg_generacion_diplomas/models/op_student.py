# -*- coding: utf-8 -*-
from odoo import models, fields, api


class OpStudent(models.Model):
    _inherit = 'op.student'

    can_generate_diploma = fields.Boolean(
        string='Puede generar diploma',
        compute='_compute_can_generate_diploma',
        store=True,
    )

    @api.depends('course_detail_ids.state', 'course_detail_ids.grade', 'course_detail_ids.final_grade')
    def _compute_can_generate_diploma(self):
        """
        The button to launch the diploma wizard should only be visible when
        the student has at least one course line that is finished or already
        carries a final grade.  Depending on the installation, the final grade
        field may be named differently or be part of a different module; the
        method checks for the most common attribute names.
        """
        for student in self:
            ok = False
            for sc in student.course_detail_ids:
                # state-based rule: course must be finished
                if sc.state == 'finished':
                    ok = True
                    break
                # grade-based rules (if those fields exist and are truthy)
                if hasattr(sc, 'grade') and sc.grade:
                    ok = True
                    break
                if hasattr(sc, 'final_grade') and sc.final_grade:
                    ok = True
                    break
            student.can_generate_diploma = ok
