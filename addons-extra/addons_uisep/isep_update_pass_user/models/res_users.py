# -*- coding: utf-8 -*-
import logging
import random
import string
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    new_password_user = fields.Char(string='Nueva Contraseña', help='Ingresa una nueva contraseña', copy=False)

    def _generate_random_password(self, length=10):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choices(characters, k=length))

    @api.model_create_multi
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get('password'):
                pwd = self._generate_random_password(10)
                vals['password'] = pwd
                vals['new_password_user'] = pwd
            else:
                pass

        users = super().create(vals_list)
        return users
    

