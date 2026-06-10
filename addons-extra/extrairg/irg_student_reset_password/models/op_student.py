# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class OpStudent(models.Model):
    _inherit = 'op.student'

    def action_generate_password(self):
        """
        Genera una nueva contraseña aleatoria para el usuario de Odoo vinculado al estudiante.
        Llama al método del modelo res.users mediante sudo para elevar privilegios del Back Office.
        """
        self.ensure_one()
        if not self.user_id:
            raise UserError(_("Este estudiante no tiene un usuario de Odoo vinculado. No se puede generar una contraseña."))
        
        # Se usa sudo() porque los usuarios del Back Office usualmente no tienen permisos de escritura
        # directos en la configuración o edición de contraseñas de res.users.
        return self.user_id.sudo().action_generate_password()
