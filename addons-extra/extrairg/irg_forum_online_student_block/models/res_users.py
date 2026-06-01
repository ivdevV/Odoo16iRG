# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.osv import expression


class ResUsers(models.Model):
    _inherit = 'res.users'

    irg_forum_online_blocked = fields.Boolean(
        string='Bloqueado en foros de campus por online',
        compute='_compute_irg_forum_online_block',
    )
    irg_forum_online_blocked_batch_ids = fields.Many2many(
        'op.batch',
        compute='_compute_irg_forum_online_block',
        string='Lotes online bloqueados para foros',
    )
    irg_forum_online_blocked_course_ids = fields.Many2many(
        'op.course',
        compute='_compute_irg_forum_online_block',
        string='Cursos online bloqueados para foros',
    )

    def _compute_irg_forum_online_block(self):
        for user in self:
            online_batches = user._irg_forum_online_candidate_batches().filtered(
                lambda batch: user._irg_forum_is_blocked_online_batch(batch)
            )
            user.irg_forum_online_blocked_batch_ids = online_batches
            user.irg_forum_online_blocked_course_ids = online_batches.mapped('course_id')
            user.irg_forum_online_blocked = bool(online_batches)

    def _irg_forum_online_candidate_batches(self):
        self.ensure_one()
        # sudo: portal users cannot reliably read academic enrollment records;
        # this only computes a boolean/batch set for access control decisions.
        user = self.sudo()
        batches = user.op_batch_ids | user.forum_effective_batch_ids

        student_domain = [('user_id', '=', user.id)]
        if user.partner_id:
            student_domain = ['|', ('user_id', '=', user.id), ('partner_id', '=', user.partner_id.id)]
        # sudo: portal users cannot read op.student, but the result is only used to compute forum restrictions.
        students = self.env['op.student'].sudo().search(student_domain)

        admission_clauses = []
        if user.partner_id:
            admission_clauses.append([('partner_id', '=', user.partner_id.id)])
        if students:
            admission_clauses.append([('student_id', 'in', students.ids)])
        if admission_clauses:
            # sudo: admissions are academic records used only to derive blocking batches for access control.
            admissions = self.env['op.admission'].sudo().search(
                expression.AND([
                    [('batch_id', '!=', False)],
                    expression.OR(admission_clauses),
                ])
            )
            batches |= admissions.mapped('batch_id')

        if students:
            # sudo: student course rows are read-only inputs for the computed forum restriction fields.
            student_courses = self.env['op.student.course'].sudo().search([
                ('student_id', 'in', students.ids),
                ('batch_id', '!=', False),
                ('state', '!=', 'finished'),
            ])
            batches |= student_courses.mapped('batch_id')

        return batches

    @staticmethod
    def _irg_forum_is_blocked_online_batch(batch):
        code = (batch.code or '').upper()
        return bool(code and 'ONL' in code and 'MONL' not in code)