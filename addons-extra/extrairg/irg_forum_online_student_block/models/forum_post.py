# -*- coding: utf-8 -*-

from markupsafe import escape

from odoo import _, api, models
from odoo.exceptions import UserError


class ForumPost(models.Model):
    _inherit = 'forum.post'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # sudo: read forum visibility metadata before denying portal post creation with a controlled error.
            forum = self._irg_forum_from_create_vals(vals).sudo()
            if forum and forum._irg_user_is_blocked_from_forum(self.env.user):
                raise UserError(_('Los alumnos online no pueden publicar en los foros del campus.'))
        return super().create(vals_list)

    def _irg_forum_from_create_vals(self, vals):
        forum = self.env['forum.forum']
        forum_id = vals.get('forum_id')
        if forum_id:
            forum = forum.browse(forum_id)
        elif vals.get('parent_id'):
            # sudo: resolve the parent thread forum to enforce the same posting rule on replies.
            forum = self.browse(vals['parent_id']).sudo().forum_id
        return forum.exists()

    def _notify_forum_followers_on_new_post(self):
        self.ensure_one()

        if self.parent_id:
            return
        if self.state and self.state != 'active':
            return

        # sudo: read forum notification settings and followers for server-side recipient filtering.
        forum = self.forum_id.sudo()
        if not forum:
            return
        if 'email_notify_enabled' in forum._fields and not forum.email_notify_enabled:
            return
        if 'notify_students_email' in forum._fields and not forum.notify_students_email:
            return

        follower_partners = forum.message_partner_ids
        if not follower_partners:
            return

        author_partner = self.create_uid.partner_id
        recipients = follower_partners - author_partner
        recipients = recipients.filtered(lambda partner: partner.active and partner.email)
        recipients = forum._irg_filter_online_blocked_partners(recipients)
        if not recipients:
            return

        # sudo: system configuration parameters are not readable by portal users.
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        post_url = '%s%s' % (base_url, self.website_url or '')

        subject = _('New post in forum: %s') % (forum.name or '')
        body = _(
            'A new publication was created in <b>%(forum)s</b>: '
            '<a href="%(url)s">%(title)s</a>'
        ) % {
            'forum': escape(forum.name or ''),
            'url': escape(post_url),
            'title': escape(self.name or _('View post')),
        }

        email_from = (
            self.env.company.email
            or self.env.company.partner_id.email
            or self.env.user.email
            or False
        )
        # sudo: queue notification emails on behalf of the forum subsystem.
        MailMail = self.env['mail.mail'].sudo()
        for partner in recipients:
            MailMail.create({
                'subject': subject,
                'body_html': body,
                'email_to': partner.email,
                'email_from': email_from,
                'auto_delete': True,
            })