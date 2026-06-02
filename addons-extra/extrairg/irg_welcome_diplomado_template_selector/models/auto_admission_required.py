# -*- coding: utf-8 -*-

from odoo import fields, models


class AutoAdmissionRequired(models.Model):
    _inherit = 'auto.admission.required'

    welcome_template_diplomado_id = fields.Many2one(
        comodel_name='mail.template',
        string='Plantilla bienvenida Diplomados',
        domain="[('model','=','op.admission')]",
        help='Plantilla usada para admisiones cuyo lote o categoria empieza por DI.',
    )
