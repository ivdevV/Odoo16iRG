from markupsafe import escape

from odoo import _, api, models


class ForumPost(models.Model):
    _inherit = "forum.post"

    @api.model_create_multi
    def create(self, vals_list):
        posts = super().create(vals_list)
        if self.env.context.get("install_mode"):
            return posts

        for post in posts:
            post._notify_forum_followers_on_new_post()
        return posts

    def _notify_forum_followers_on_new_post(self):
        self.ensure_one()

        if self.parent_id:
            return
        if self.state and self.state != "active":
            return

        forum = self.forum_id.sudo()
        if not forum:
            return
        if "notify_students_email" in forum._fields and not forum.notify_students_email:
            return

        follower_partners = forum.message_partner_ids
        if not follower_partners:
            return

        author_partner = self.create_uid.partner_id
        recipients = follower_partners - author_partner
        recipients = recipients.filtered(lambda partner: partner.active and partner.email)
        if not recipients:
            return

        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        post_url = "%s%s" % (base_url, self.website_url or "")

        subject = _("New post in forum: %s") % (forum.name or "")
        body = _(
            "A new publication was created in <b>%(forum)s</b>: "
            "<a href=\"%(url)s\">%(title)s</a>"
        ) % {
            "forum": escape(forum.name or ""),
            "url": escape(post_url),
            "title": escape(self.name or _("View post")),
        }

        email_from = (
            self.env.company.email
            or self.env.company.partner_id.email
            or self.env.user.email
            or False
        )
        MailMail = self.env["mail.mail"].sudo()
        for partner in recipients:
            MailMail.create({
                "subject": subject,
                "body_html": body,
                "email_to": partner.email,
                "email_from": email_from,
                "auto_delete": True,
            })
