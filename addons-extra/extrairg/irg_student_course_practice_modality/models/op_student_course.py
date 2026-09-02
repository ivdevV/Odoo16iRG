# -*- coding: utf-8 -*-

from odoo import fields, models


class OpStudentCourse(models.Model):
    _inherit = 'op.student.course'

    irg_practice_center_type_id = fields.Many2one(
        'practice.center.type',
        string='Modalidad de prácticas',
        tracking=True,
        help='Tipo de prácticas de esta matrícula. Lo rellena la última '
             'solicitud aprobada o posterior y secretaría puede corregirlo.',
    )
