from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    op_batch_ids = fields.Many2many(
        'op.batch',
        'res_users_forum_op_batch_rel',
        'user_id',
        'batch_id',
        string='Forum Allowed Batches',
        help='Batches that this user can access in forum posts and forums.',
    )

    forum_effective_batch_ids = fields.Many2many(
        'op.batch',
        compute='_compute_forum_effective_batch_ids',
        string='Forum Effective Batches',
        help='Union of direct forum batches and batches from admissions for this user.',
    )

    forum_effective_course_ids = fields.Many2many(
        'op.course',
        compute='_compute_forum_effective_batch_ids',
        string='Forum Effective Courses',
        help='Courses linked to this user from admissions and student courses.',
    )

    def _compute_forum_effective_batch_ids(self):
        Admission = self.env['op.admission'].sudo()
        Student = self.env['op.student'].sudo()
        StudentCourse = self.env['op.student.course'].sudo()
        for user in self:
            student_ids = Student.search([
                '|',
                ('user_id', '=', user.id),
                ('partner_id', '=', user.partner_id.id),
            ])

            admission_batch_ids = Admission.search([
                '|',
                ('partner_id', '=', user.partner_id.id),
                ('student_id', 'in', student_ids.ids),
                ('batch_id', '!=', False),
            ]).mapped('batch_id')

            admission_course_ids = Admission.search([
                '|',
                ('partner_id', '=', user.partner_id.id),
                ('student_id', 'in', student_ids.ids),
                ('course_id', '!=', False),
            ]).mapped('course_id')

            student_course_batch_ids = StudentCourse.search([
                ('student_id', 'in', student_ids.ids),
                ('batch_id', '!=', False),
                ('state', '!=', 'finished'),
            ]).mapped('batch_id')

            student_course_ids = StudentCourse.search([
                ('student_id', 'in', student_ids.ids),
                ('course_id', '!=', False),
                ('state', '!=', 'finished'),
            ]).mapped('course_id')

            user.forum_effective_batch_ids = user.op_batch_ids | admission_batch_ids | student_course_batch_ids
            user.forum_effective_course_ids = admission_course_ids | student_course_ids
