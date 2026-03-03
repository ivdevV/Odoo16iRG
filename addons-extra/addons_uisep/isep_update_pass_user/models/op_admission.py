# -*- coding: utf-8 -*-
from odoo import api, fields, models


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    new_password_user = fields.Char(
        string='Nueva Contraseña Usuario',
        compute='_compute_new_password_user',
        readonly=True,
    )

    @api.depends('student_id', 'student_id.user_id', 'student_id.user_id.new_password_user')
    def _compute_new_password_user(self):
        for admission in self:
            student_user = admission.student_id.user_id.sudo()
            admission.new_password_user = student_user.new_password_user or ''
