# -*- coding: utf-8 -*-

from odoo import models, fields


class OpUniversity(models.Model):
    _name = "op.university"
    _description = "Openeducat university"

    name = fields.Char('Nombre', size=128, required=True)
#    code = fields.Char('Codigo', size=32, required=True)
    _sql_constraints = [('unique_university', 'unique (name)', 'Ya existe la Universidad')]

