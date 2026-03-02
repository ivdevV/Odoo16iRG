# -*- coding: utf-8 -*-

from odoo import fields, models


class GeneratePasswordWizard(models.TransientModel):
    _name = 'isep.generate.password.wizard'
    _description = 'Generated Password Wizard'

    user_id = fields.Many2one('res.users', string='Usuario', readonly=True)
    generated_password = fields.Char(string='Nueva contraseña', readonly=True)
