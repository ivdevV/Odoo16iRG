# -*- coding: utf-8 -*-
from odoo import models, fields


class OpSubject(models.Model):
    _inherit = 'op.subject'

    gradebook_id = fields.Many2one(
        'app.gradebook',
        string='Calificaciones template',
        default=lambda self: self.env.ref(
            'irg_gradebook_exam_as_final.gradebook_template_solo_examen',
            raise_if_not_found=False,
        ),
    )
