from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    forum_batch_ids = fields.Many2many(
        'forum.visibility.batch',
        'res_users_forum_visibility_batch_rel',
        'user_id',
        'batch_id',
        string='Forum Batches',
        help='Batches that this user can access in the forum.',
    )
