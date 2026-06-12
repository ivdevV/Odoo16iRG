# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AppGradebookStudent(models.Model):
    _inherit = 'app.gradebook.student'

    gradebook_id = fields.Many2one(
        'app.gradebook',
        string='Calificaciones template',
        store=True,
        compute="compute_gradebook_id",
        readonly=False,
        tracking=True,
    )

    @api.depends('course_id')
    def compute_gradebook_id(self):
        # Conserva el valor puesto a mano; solo rellena desde el curso si está vacío
        for rec in self:
            rec.gradebook_id = rec.gradebook_id or rec.course_id.gradebook_id
