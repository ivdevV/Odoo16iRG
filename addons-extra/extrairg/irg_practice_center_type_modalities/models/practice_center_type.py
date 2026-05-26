# -*- coding: utf-8 -*-

from odoo import fields, models


class PracticeCenterType(models.Model):
    _inherit = 'practice.center.type'

    type_of_practice = fields.Selection(
        selection_add=[
            ('on_site', 'Presencial en España'),
            ('on_site_origin', 'Presencial País de Origen'),
            ('validation', 'Convalidación por experiencia'),
            ('tfm_validation', 'Convalidación por TFM'),
        ],
    )
