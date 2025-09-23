# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit= "product.template"

    is_titulacion = fields.Boolean(string="ver titulacion", default=False)