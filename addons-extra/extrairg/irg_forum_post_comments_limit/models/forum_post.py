from odoo import _, api, fields, models
from odoo.exceptions import UserError

class ForumPost(models.Model):
    _inherit = 'forum.post'

    allow_comments = fields.Boolean(
        string="Allow Comments / Replies",
        default=True,
        help="If checked, users can reply or comment on this forum post. If unchecked, the reply and comment buttons will be hidden."
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            parent_id = vals.get('parent_id')
            if parent_id:
                parent_post = self.browse(parent_id)
                if parent_post.exists() and not parent_post.allow_comments:
                    raise UserError(_("Comments/replies are disabled for this post."))
        return super().create(vals_list)

    def _compute_can_answer(self):
        super()._compute_can_answer()
        for post in self:
            if not post.allow_comments:
                post.can_answer = False

    def _compute_can_comment(self):
        super()._compute_can_comment()
        for post in self:
            if not post.allow_comments:
                post.can_comment = False
