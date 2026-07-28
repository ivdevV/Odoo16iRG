# -*- coding: utf-8 -*-

from odoo import fields, models


class PracticeRequest(models.Model):
    _inherit = 'practice.request'

    irg_preferred_quarter = fields.Selection(
        selection=[
            ('marzo_mayo', 'Marzo a Mayo'),
            ('junio_agosto', 'Junio a Agosto'),
            ('septiembre_noviembre', 'Septiembre a Noviembre'),
            ('diciembre_febrero', 'Diciembre a Febrero'),
        ],
        string='Trimestre preferente para iniciar las prácticas',
        help='Trimestre preferente seleccionado por el alumno para el inicio de sus prácticas',
    )
