# -*- coding: utf-8 -*-

from odoo import models, fields, _

class OpSubject(models.Model):
    _inherit = 'op.subject'

    irg_modality = fields.Selection([
        ('presencial', 'Presencial'),
        ('online', 'Online')
    ], string='Modalidad', default='online', help=_("Modalidad de la asignatura para clasificar en el diplomado."))

