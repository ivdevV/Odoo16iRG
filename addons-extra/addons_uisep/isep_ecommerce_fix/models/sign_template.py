# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SignTemplateInherit(models.Model):
    _inherit = 'sign.template'


    def create_link_sign(self):
        self.ensure_one()

        shared_sign_request = self.sign_request_ids.filtered(
            lambda sr: sr.state == 'shared' and sr.create_uid == self.env.user
        )
        if shared_sign_request:
            return shared_sign_request

        if len(self.sign_item_ids.mapped('responsible_id')) > 1:
            raise ValidationError(_("You cannot share this document by link, because it has fields to be filled by different roles. Use Send button instead."))

        try:
            admin_user = self.env.ref('base.user_admin')
            admin_env = self.env(user=admin_user.id)
            admin_self = self.with_env(admin_env)
            role_id = self.sign_item_ids.responsible_id.id
            if not role_id:
                default_role = self.env.ref('sign.sign_item_role_default')
                role_id = default_role.id if default_role else None


            shared_sign_request = admin_env['sign.request'].with_context(no_sign_mail=True).create({
                'template_id': self.id,
                'request_item_ids': [Command.create({'role_id': role_id})],
                'reference': "%s-%s" % (self.name, _("Shared")),
                'state': 'shared',
            })


        except Exception as e:
            raise

        return shared_sign_request