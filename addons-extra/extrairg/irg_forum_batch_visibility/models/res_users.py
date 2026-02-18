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
