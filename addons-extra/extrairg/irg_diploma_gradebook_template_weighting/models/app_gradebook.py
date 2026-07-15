# -*- coding: utf-8 -*-
from odoo import fields, models


class AppGradebook(models.Model):
    _inherit = 'app.gradebook'

    final_calculation_mode = fields.Selection(
        selection=[
            ('standard', 'Calculo estandar'),
            (
                'diploma_50_50',
                'Diplomado: presencial 50% + resto 50%',
            ),
        ],
        string='Calculo final',
        default='standard',
        required=True,
        tracking=True,
        help=(
            'El modo especial solo se aplica cuando el curso tambien se '
            'identifica como Diplomado y existe un unico modulo presencial.'
        ),
    )
