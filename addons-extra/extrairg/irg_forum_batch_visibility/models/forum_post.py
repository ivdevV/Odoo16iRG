from odoo import api, fields, models


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

    @api.model_create_multi
    def create(self, vals_list):
        posts = super().create(vals_list)
        pending_posts = posts.filtered(lambda post: post.state == 'pending')
        if pending_posts:
            pending_posts.sudo().write({
                'state': 'active',
                'active': True,
            })
        return posts
