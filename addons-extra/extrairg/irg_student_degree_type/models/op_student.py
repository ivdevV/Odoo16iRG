# -*- coding: utf-8 -*-

from odoo import fields, models


class OpStudent(models.Model):
    _inherit = 'op.student'

    irg_degree_type_ids = fields.Many2many(
        'irg.student.degree.type',
        'op_student_irg_degree_type_rel',
        'student_id',
        'degree_type_id',
        string='Tipo de titulación',
    )
