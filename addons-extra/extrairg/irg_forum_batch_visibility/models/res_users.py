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

    def _compute_forum_effective_batch_ids(self):
        Admission = self.env['op.admission'].sudo()
        for user in self:
            admission_batch_ids = Admission.search([
                ('partner_id', '=', user.partner_id.id),
                ('batch_id', '!=', False),
            ]).mapped('batch_id')
            user.forum_effective_batch_ids = user.op_batch_ids | admission_batch_ids
