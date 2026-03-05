from odoo import models, fields

class ForumPost(models.Model):
    _inherit = 'forum.post'

    allow_comments = fields.Boolean(
        string="Allow Comments / Replies",
        default=True,
        help="If checked, users can reply or comment on this forum post. If unchecked, the reply and comment buttons will be hidden."
    )
