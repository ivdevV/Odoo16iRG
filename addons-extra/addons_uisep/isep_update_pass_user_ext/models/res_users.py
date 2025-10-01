# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'


    def action_generate_password(self):
        for user in self:
            if not user.active:
                raise UserError(_("Cannot generate a password for inactive users."))
            pwd = user._generate_random_password(10)
            user.write({'password': pwd, 'new_password_user': pwd})

            user.partner_id.message_post(body=_("Se generó una nueva contraseña para el usuario."))

            msg = _("Nueva contraseña: %s") % pwd if len(self) == 1 else _("Contraseñas generadas.")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Contraseña actualizada'),
                    'message': msg,
                    'sticky': False,
                    'type': 'success',
                }
            }
