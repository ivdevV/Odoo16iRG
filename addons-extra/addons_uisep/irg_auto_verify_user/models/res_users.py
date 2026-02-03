# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# Valor de karma que Odoo asigna cuando un usuario verifica su email
# Definido en website_profile/models/res_users.py
VALIDATION_KARMA_GAIN = 3


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override para auto-verificar usuarios al crearlos.
        
        El módulo website_profile considera que un usuario está verificado
        si tiene karma > 0. Asignamos VALIDATION_KARMA_GAIN (3) para que
        no aparezca el mensaje "No se ha verificado su cuenta".
        """
        users = super().create(vals_list)
        
        # Auto-verificar asignando karma a los nuevos usuarios
        for user in users:
            if user.karma == 0:
                try:
                    user.sudo().write({'karma': VALIDATION_KARMA_GAIN})
                    _logger.info(
                        "Usuario %s (ID: %s) auto-verificado con karma=%s",
                        user.login, user.id, VALIDATION_KARMA_GAIN
                    )
                except Exception as e:
                    _logger.warning(
                        "No se pudo auto-verificar usuario %s: %s",
                        user.login, str(e)
                    )
        
        return users

    def action_auto_verify_users(self):
        """
        Acción para auto-verificar usuarios existentes que tengan karma = 0.
        Puede ejecutarse manualmente desde la vista de usuarios.
        """
        users_to_verify = self.filtered(lambda u: u.karma == 0)
        if users_to_verify:
            users_to_verify.sudo().write({'karma': VALIDATION_KARMA_GAIN})
            _logger.info(
                "Auto-verificados %s usuarios existentes",
                len(users_to_verify)
            )
        return True
