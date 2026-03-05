import hashlib
import hmac
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class ForumEmailUnsubscribe(http.Controller):
    """Public endpoints for one-click forum email (un)subscribe.

    Each link carries an HMAC token so that only the intended recipient
    can change their own subscription status — no login required.
    """

    # ------------------------------------------------------------------
    # Token verification
    # ------------------------------------------------------------------

    @staticmethod
    def _verify_token(db_secret, user_id, forum_id, token):
        expected = 'forum-unsub-%d-%d' % (user_id, forum_id)
        computed = hmac.new(
            db_secret.encode('utf-8'),
            expected.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()[:32]
        return hmac.compare_digest(computed, token)

    # ------------------------------------------------------------------
    # Unsubscribe
    # ------------------------------------------------------------------

    @http.route(
        '/forum/email/unsubscribe',
        type='http',
        auth='public',
        website=True,
        methods=['GET'],
    )
    def forum_email_unsubscribe(self, uid=0, fid=0, token='', **kw):
        uid, fid = int(uid), int(fid)
        db_secret = (
            request.env['ir.config_parameter']
            .sudo()
            .get_param('database.secret', '')
        )

        if not self._verify_token(db_secret, uid, fid, token):
            _logger.warning(
                'Invalid unsubscribe token for uid=%s fid=%s', uid, fid,
            )
            return request.render(
                'irg_forum_email_notify.forum_unsubscribe_error', {},
            )

        user = request.env['res.users'].sudo().browse(uid)
        forum = request.env['forum.forum'].sudo().browse(fid)

        if not user.exists() or not forum.exists():
            return request.render(
                'irg_forum_email_notify.forum_unsubscribe_error', {},
            )

        # Add forum to the user's opt-out list (idempotent)
        if forum not in user.forum_email_optout_ids:
            user.write({'forum_email_optout_ids': [(4, forum.id)]})
            _logger.info(
                'User %s opted out of forum email notifications for "%s"',
                user.login, forum.name,
            )

        base_url = (
            request.env['ir.config_parameter']
            .sudo()
            .get_param('web.base.url', '')
        )
        resubscribe_url = (
            '%s/forum/email/resubscribe?uid=%d&fid=%d&token=%s'
            % (base_url, uid, fid, token)
        )

        return request.render(
            'irg_forum_email_notify.forum_unsubscribe_done',
            {
                'forum_name': forum.name,
                'resubscribe_url': resubscribe_url,
            },
        )

    # ------------------------------------------------------------------
    # Resubscribe
    # ------------------------------------------------------------------

    @http.route(
        '/forum/email/resubscribe',
        type='http',
        auth='public',
        website=True,
        methods=['GET'],
    )
    def forum_email_resubscribe(self, uid=0, fid=0, token='', **kw):
        uid, fid = int(uid), int(fid)
        db_secret = (
            request.env['ir.config_parameter']
            .sudo()
            .get_param('database.secret', '')
        )

        if not self._verify_token(db_secret, uid, fid, token):
            _logger.warning(
                'Invalid resubscribe token for uid=%s fid=%s', uid, fid,
            )
            return request.render(
                'irg_forum_email_notify.forum_unsubscribe_error', {},
            )

        user = request.env['res.users'].sudo().browse(uid)
        forum = request.env['forum.forum'].sudo().browse(fid)

        if not user.exists() or not forum.exists():
            return request.render(
                'irg_forum_email_notify.forum_unsubscribe_error', {},
            )

        # Remove forum from the user's opt-out list (idempotent)
        if forum in user.forum_email_optout_ids:
            user.write({'forum_email_optout_ids': [(3, forum.id)]})
            _logger.info(
                'User %s re-subscribed to forum email notifications for "%s"',
                user.login, forum.name,
            )

        return request.render(
            'irg_forum_email_notify.forum_resubscribe_done',
            {
                'forum_name': forum.name,
            },
        )
