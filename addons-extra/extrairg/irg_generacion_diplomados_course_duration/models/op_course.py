# -*- coding: utf-8 -*-
from odoo import fields, models


class OpCourse(models.Model):
    _inherit = 'op.course'

    irg_diplomado_duration_hours = fields.Integer(
        string='Horas del Diplomado',
        help='Duracion en horas que se imprimira en el diploma de diplomado.',
    )
    irg_diplomado_duration_ects = fields.Float(
        string='ECTS del Diplomado',
        help='Creditos ECTS que se imprimiran en el diploma de diplomado.',
    )
