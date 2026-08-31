# -*- coding: utf-8 -*-

from odoo import fields, models


class IrgStudentDegreeType(models.Model):
    _name = 'irg.student.degree.type'
    _description = 'Tipo de titulación'
    _order = 'name'

    name = fields.Char(
        string='Nombre',
        required=True,
        translate=True,
    )
    color = fields.Integer(
        string='Color',
        default=0,
    )
