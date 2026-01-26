# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PracticeRequestFix(models.Model):
    _inherit = 'practice.request'

    # Sobrescribir user_id para agregar default del usuario actual
    user_id = fields.Many2one(
        'res.users',
        string="Usuario Estudiante",
        required=True,
        default=lambda self: self.env.user,
    )

    # Sobrescribe op_student_id para que sea computado desde user_id
    op_student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        compute='_compute_student_from_user',
        store=True,
        help="Estudiante asociado al usuario. Se obtiene automáticamente."
    )

    @api.depends('user_id')
    def _compute_student_from_user(self):
        """Obtiene el estudiante a partir del usuario"""
        for record in self:
            if record.user_id:
                student = self.env['op.student'].sudo().search([
                    ('user_id', '=', record.user_id.id)
                ], limit=1)
                record.op_student_id = student.id if student else False
            else:
                record.op_student_id = False

    @api.onchange('user_id')
    def _onchange_user_fill_data(self):
        """Llena automáticamente los datos cuando se selecciona un usuario"""
        if self.user_id:
            student = self.env['op.student'].sudo().search([
                ('user_id', '=', self.user_id.id)
            ], limit=1)
            if student:
                self.name = student.name or ''
                self.email = student.email or self.user_id.email or ''
            else:
                self.name = self.user_id.name or ''
                self.email = self.user_id.email or ''
            # Limpiar campos dependientes
            self.op_admission_id = False
            self.course_id = False

