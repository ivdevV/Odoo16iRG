# -*- coding: utf-8 -*-
from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Combine selection values from moodle connector and isep_openeducat_sale to avoid selection conflicts,
    # and clear the default value to avoid ValueError when creating partners without gender.
    gender = fields.Selection([
        ('m', 'Masculino'),
        ('f', 'Femenino'),
        ('o', 'Otro'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('not-sure', 'Not Sure')
    ], string='Género', default=False)
