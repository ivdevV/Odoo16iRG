from odoo import fields, models


class IrgForumNoticeSeen(models.Model):
    _name = 'irg.forum.notice.seen'
    _description = 'Forum Notice Seen by User'
    _rec_name = 'post_id'

    user_id = fields.Many2one('res.users', required=True, index=True, ondelete='cascade')
    course_id = fields.Many2one('op.course', required=True, index=True, ondelete='cascade')
    post_id = fields.Many2one('forum.post', required=True, index=True, ondelete='cascade')
    seen_at = fields.Datetime(required=True, default=fields.Datetime.now)

    _sql_constraints = [
        ('irg_forum_notice_seen_unique', 'unique(user_id, course_id, post_id)', 'Seen state already exists for this user/course/post.'),
    ]
