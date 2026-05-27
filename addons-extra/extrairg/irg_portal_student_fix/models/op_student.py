# -*- coding: utf-8 -*-
from odoo import models, fields, api

class OpStudent(models.Model):
    _inherit = 'op.student'

    @api.depends('op_course_ids', 'op_course_ids.completion_porc')
    def _compute_total_completion(self):
        for student in self:
            total_approved = 0
            total_subjects = 0

            # Use sudo() to query op.student.course, op.subject and app.gradebook.subject
            # under portal/student user transactions.
            for course in student.sudo().op_course_ids:
                subjects = self.env['op.subject'].sudo().search([
                    ('course_id', '=', course.course_id.id),
                    ('subject_type', '=', 'compulsory')
                ])
                total_subjects += len(subjects)

                approved = self.env['app.gradebook.subject'].sudo().search_count([
                    ('gradebook_student_id.student_id', '=', student.id),
                    ('gradebook_student_id.course_id', '=', course.course_id.id),
                    ('op_subject_id', 'in', subjects.ids),
                    ('final_subject_note', '>=', 8)
                ])
                total_approved += approved
            if total_subjects > 0:
                student.total_completion_porc = (total_approved / total_subjects) * 100
            else:
                student.total_completion_porc = 0.0


class OpStudentCourse(models.Model):
    _inherit = 'op.student.course'

    def _compute_advance_search(self):
        for rec in self:
            rec.completion_porc = 0.0
            rec_sudo = rec.sudo()
            if rec_sudo.student_id and rec_sudo.course_id:
                subject_count = self.env['op.subject'].sudo().search_count([
                    ('course_id', '=', rec_sudo.course_id.id),
                    ('subject_type', '=', 'compulsory')
                ])
                
                gradebook_subject_count = self.env['app.gradebook.subject'].sudo().search_count([
                    ('gradebook_student_id.student_id', '=', rec_sudo.student_id.id),
                    ('op_subject_id.subject_type', '=', 'compulsory'),
                    ('gradebook_student_id.course_id', '=', rec_sudo.course_id.id),
                    ('final_subject_note', '>=', 8)  
                ])
                
                if gradebook_subject_count > 0 and subject_count > 0:
                    rec.completion_porc = (gradebook_subject_count / subject_count) * 100
                else:
                    rec.completion_porc = 0.0
