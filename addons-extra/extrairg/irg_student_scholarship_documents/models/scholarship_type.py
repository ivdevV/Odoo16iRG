# -*- coding: utf-8 -*-

from odoo import fields, models


class IrgScholarshipType(models.Model):
    _name = 'irg.scholarship.type'
    _description = 'Tipo de beca IRG'
    _order = 'sequence, name, id'

    name = fields.Char(string='Tipo de beca', required=True, translate=True)
    description = fields.Text(string='Descripcion', translate=True)
    sequence = fields.Integer(string='Secuencia', default=10)
    active = fields.Boolean(string='Activo', default=True)
