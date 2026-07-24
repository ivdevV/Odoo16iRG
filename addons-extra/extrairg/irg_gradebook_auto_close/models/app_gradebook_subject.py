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
        "gradebook_result_ids",
        "gradebook_result_ids.survey_type",
    )
    def compute_data_show(self):
        super().compute_data_show()
        for record in self:
            types_with_results = (
                set(record.gradebook_result_ids.mapped("survey_type"))
                if record.gradebook_result_ids
                else set()
            )
            student_template = record.gradebook_student_id.gradebook_id
            if not student_template:
                if types_with_results:
                    if "assignment" in types_with_results:
                        record.show_assignment = True
                    if "exam" in types_with_results:
                        record.show_exam = True
                    if "interaction" in types_with_results:
                        record.show_interaction = True
                    if "foro" in types_with_results:
                        record.show_foro = True
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
            effective_types = (student_types & line_types) | types_with_results

            record.show_assignment = "assignment" in effective_types
            record.show_exam = "exam" in effective_types
            record.show_interaction = "interaction" in effective_types
            record.show_foro = "foro" in effective_types
