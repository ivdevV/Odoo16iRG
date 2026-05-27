# -*- coding: utf-8 -*-

from odoo import models


class MailMail(models.Model):
    _inherit = 'mail.mail'

    def _send(self, auto_commit=False, raise_exception=False, smtp_session=None, **kwargs):
        service = self.env['irg.mail.n8n.service']
        if not service._is_enabled():
            return super()._send(
                auto_commit=auto_commit,
                raise_exception=raise_exception,
                smtp_session=smtp_session,
                **kwargs,
            )

        result = True
        for mail in self:
            if mail.state == 'sent':
                continue
            sent = service._dispatch_mail(mail)
            result = result and sent
            if auto_commit:
                self.env.cr.commit()
        return result

    def send(self, auto_commit=False, raise_exception=False):
        service = self.env['irg.mail.n8n.service']
        if not service._is_enabled():
            return super().send(auto_commit=auto_commit, raise_exception=raise_exception)

        return self._send(auto_commit=auto_commit, raise_exception=raise_exception)