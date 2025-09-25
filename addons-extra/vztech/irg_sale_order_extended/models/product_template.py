# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    formation_type = fields.Selection(selection=[('formation', 'Formation'), ('registration', 'Registration'), (
        'discount_registration', 'Discount Registration'), ('officialdom', 'Officialdom'), ('bonus', 'Bonus')], string='Formation Type')
