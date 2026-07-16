# -*- coding: utf-8 -*-

from odoo import api, models


class AppGradebookSubject(models.Model):
    _inherit = "app.gradebook.subject"

    @api.depends(
        "gradebook_id",
        "gradebook_id.gradebook_template_ids",
        "gradebook_id.gradebook_template_ids.type",
        "gradebook_student_id.gradebook_id",
        "gradebook_student_id.gradebook_id.gradebook_template_ids",
        "gradebook_student_id.gradebook_id.gradebook_template_ids.type",
    )
    def compute_data_show(self):
        super().compute_data_show()
        for record in self:
            student_template = record.gradebook_student_id.gradebook_id
            if not student_template:
                continue

            student_types = set(
                student_template.gradebook_template_ids.mapped("type")
            )
            line_template = record.gradebook_id
            line_types = (
                set(line_template.gradebook_template_ids.mapped("type"))
                if line_template
                else student_types
            )
            effective_types = student_types & line_types

            record.show_assignment = "assignment" in effective_types
            record.show_exam = "exam" in effective_types
            record.show_interaction = "interaction" in effective_types
            record.show_foro = "foro" in effective_types
