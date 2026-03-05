import hashlib
import hmac
import logging

from markupsafe import Markup

from odoo import api, models

_logger = logging.getLogger(__name__)


class ForumPost(models.Model):
    _inherit = 'forum.post'

    # ------------------------------------------------------------------
    # Create override — queue email notifications
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        posts = super().create(vals_list)
        for post in posts:
            try:
                post.sudo()._send_forum_email_notification()
            except Exception:
                _logger.exception(
                    'Failed to queue forum email notifications for post %s',
                    post.id,
                )
        return posts

    # ------------------------------------------------------------------
    # Email notification logic
    # ------------------------------------------------------------------

    def _send_forum_email_notification(self):
        """Create ``mail.mail`` records for all eligible recipients.

        The mails are left in *outgoing* state so that Odoo's built-in
        mail scheduler cron sends them asynchronously (usually within a
        minute).  This avoids blocking the post-creation request.
        """
        self.ensure_one()
        forum = self.forum_id

        if not forum.email_notify_enabled:
            return

        author_partner = self.create_uid.partner_id
        partners = forum._get_notification_recipients(
            exclude_partner=author_partner,
        )

        if not partners:
            _logger.info(
                'No recipients for forum email on post %s (forum %s)',
                self.id, forum.name,
            )
            return

        base_url = (
            self.env['ir.config_parameter']
            .sudo()
            .get_param('web.base.url', '')
        )

        # Determine thread URL and title
        if self.parent_id:
            thread_url = '%s%s' % (base_url, self.parent_id.website_url or '')
            thread_name = self.parent_id.name
            is_reply = True
        else:
            thread_url = '%s%s' % (base_url, self.website_url or '')
            thread_name = self.name
            is_reply = False

        db_secret = (
            self.env['ir.config_parameter']
            .sudo()
            .get_param('database.secret', '')
        )

        company_email = (
            self.env.company.email
            or self.env.company.partner_id.email
            or ''
        )

        author_name = self.create_uid.name or 'Anónimo'

        # Subject line
        if is_reply:
            subject = 'Nueva respuesta en %s: %s' % (forum.name, thread_name)
        else:
            subject = 'Nuevo tema en %s: %s' % (forum.name, self.name)

        MailMail = self.env['mail.mail'].sudo()
        created = 0

        for partner in partners:
            user = self.env['res.users'].sudo().search(
                [('partner_id', '=', partner.id)], limit=1,
            )
            if not user:
                # Partner exists but has no portal/internal user — skip.
                continue

            token = self._generate_unsubscribe_token(
                db_secret, user.id, forum.id,
            )
            unsubscribe_url = (
                '%s/forum/email/unsubscribe?uid=%d&fid=%d&token=%s'
                % (base_url, user.id, forum.id, token)
            )

            # Render the QWeb email template
            body_html = self.env['ir.qweb']._render(
                'irg_forum_email_notify.email_forum_post_notification',
                {
                    'post': self,
                    'post_content': Markup(self.content or ''),
                    'forum': forum,
                    'thread_url': thread_url,
                    'thread_name': thread_name,
                    'is_reply': is_reply,
                    'author_name': author_name,
                    'unsubscribe_url': unsubscribe_url,
                    'base_url': base_url,
                },
            )

            MailMail.create({
                'subject': subject,
                'body_html': str(body_html),
                'email_from': company_email,
                'email_to': partner.email,
                'auto_delete': True,
            })
            created += 1

        _logger.info(
            'Queued %d forum email notifications for post %s in forum "%s"',
            created, self.id, forum.name,
        )

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_unsubscribe_token(secret, user_id, forum_id):
        """Return an HMAC-SHA256 token (32 hex chars) for opt-out links."""
        message = 'forum-unsub-%d-%d' % (user_id, forum_id)
        return hmac.new(
            secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()[:32]
