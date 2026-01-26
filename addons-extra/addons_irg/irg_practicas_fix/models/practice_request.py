# -*- coding: utf-8 -*-
from odoo import models, fields, api


class PracticeRequestFix(models.Model):
    _inherit = 'practice.request'

    # Sobrescribe el campo user_id para que sea relacionado con el estudiante
    # En lugar de ser un campo independiente que se llena manualmente
    user_id = fields.Many2one(
        'res.users',
        string="Usuario Estudiante",
        related="op_student_id.user_id",
        store=True,
        help="Usuario del sistema asociado al estudiante. Se obtiene automáticamente desde el estudiante."
    )
