from odoo import api, models


class ForumPost(models.Model):
    _inherit = 'forum.post'

    @api.model_create_multi
    def create(self, vals_list):
        raw_ids = self.env.context.get('irg_visibility_batch_ids')
        if not isinstance(raw_ids, (list, tuple)):
            raw_ids = None
        if raw_ids and self.env.user.has_group('base.group_user'):
            for vals in vals_list:
                if vals.get('parent_id') or 'visibility_batch_ids' in vals:
                    continue
                forum = self.env['forum.forum'].browse(vals.get('forum_id')).exists()
                if not forum:
                    continue
                batch_ids = forum._irg_sanitize_web_post_batch_ids(raw_ids)
                if batch_ids:
                    vals['visibility_batch_ids'] = [(6, 0, batch_ids)]
        return super().create(vals_list)
