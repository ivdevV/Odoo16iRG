# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError

class ResUsers(models.Model):
    _inherit = 'res.users'


    def action_generate_password(self):
        last_password = False
        for user in self:
            if not user.active:
                raise UserError(_("Cannot generate a password for inactive users."))
            pwd = user._generate_random_password(10)
            user.write({'password': pwd, 'new_password_user': pwd})
            last_password = pwd

            user.partner_id.message_post(body=_("Se generó una nueva contraseña para el usuario."))

        if len(self) == 1:
            wizard = self.env['isep.generate.password.wizard'].create({
                'user_id': self.id,
                'generated_password': last_password,
            })
            return {
                'name': _('Contraseña actualizada'),
                'type': 'ir.actions.act_window',
                'res_model': 'isep.generate.password.wizard',
                'view_mode': 'form',
                'res_id': wizard.id,
                'target': 'new',
            }

        msg = _("Contraseñas generadas para %s usuarios.") % len(self)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Contraseñas actualizadas'),
                'message': msg,
                'sticky': False,
                'type': 'success',
            }
        }
