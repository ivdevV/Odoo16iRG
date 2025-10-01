# -*- coding: utf-8 -*-

from odoo import models, fields


class OpStudyType(models.Model):
    _name = "op.study.type"
    _description = "study type"

    name = fields.Char('Name', size=128, required=True)
#    code = fields.Char('Code', size=12, required=True)
    _sql_constraints = [('unique_study_type', 'unique (name)', 'Ya existe la Titulación')]

