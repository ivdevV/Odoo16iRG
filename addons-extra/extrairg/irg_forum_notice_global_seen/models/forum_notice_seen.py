import logging

from psycopg2.errors import UniqueViolation

from odoo import api, fields, models


_logger = logging.getLogger(__name__)


class IrgForumNoticeGlobalSeen(models.Model):
    _name = 'irg.forum.notice.global.seen'
    _description = 'Forum Notice Globally Seen by User'
    _rec_name = 'post_id'

    user_id = fields.Many2one(
        'res.users', required=True, index=True, ondelete='cascade'
    )
    post_id = fields.Many2one(
        'forum.post', required=True, index=True, ondelete='cascade'
    )
    seen_at = fields.Datetime(required=True, default=fields.Datetime.now)

    _sql_constraints = [
        (
            'irg_forum_notice_global_seen_unique',
            'unique(user_id, post_id)',
            'This forum notice is already seen by this user.',
        ),
    ]

    @api.model
    def _irg_is_seen(self, user_id, post_id):
        domain = [('user_id', '=', user_id), ('post_id', '=', post_id)]
        if self.sudo().search_count(domain):
            return True
        return bool(
            self.env['irg.forum.notice.seen'].sudo().search_count(domain)
        )

    @api.model
    def _irg_mark_seen(self, user_id, post_id):
        domain = [('user_id', '=', user_id), ('post_id', '=', post_id)]
        seen = self.sudo().search(domain, limit=1)
        now = fields.Datetime.now()
        if seen:
            seen.write({'seen_at': now})
            return seen
        try:
            with self.env.cr.savepoint():
                return self.sudo().create({
                    'user_id': user_id,
                    'post_id': post_id,
                    'seen_at': now,
                })
        except UniqueViolation:
            _logger.debug(
                'forum_notice_global_seen: concurrent duplicate ignored'
            )
            seen = self.sudo().search(domain, limit=1)
            if seen:
                seen.write({'seen_at': now})
            return seen
