from odoo import fields, models


class ForumPost(models.Model):
    _inherit = 'forum.post'

    visibility_batch_ids = fields.Many2many(
        'op.batch',
        'forum_post_visibility_batch_rel',
        'post_id',
        'batch_id',
        string='Visibility Batches',
        help='If empty, this post follows the forum batch rules. If set, only users in these batches can read this post.',
    )
