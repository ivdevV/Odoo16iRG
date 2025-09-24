# -*- coding: utf-8 -*-

from odoo import models, fields


class OpProfession(models.Model):
    _name = "op.profession"
    _description = "Openeducat Profession"

    name = fields.Char('Nombre', size=128, required=True)
#    code = fields.Char('Codigo', size=32, required=True)
    _sql_constraints = [('unique_profession', 'unique (name)', 'Ya existe la Profesión')]
