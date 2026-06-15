# -*- coding: utf-8 -*-

from odoo import models, fields, _

class OpCourse(models.Model):
    _inherit = 'op.course'

    irg_diplomado_subjects_presencial = fields.Text(
        string='Asignaturas Presenciales (Texto)',
        help=_("Listado de asignaturas presenciales (separadas por línea) para imprimir en el diplomado.")
    )
    irg_diplomado_subjects_online = fields.Text(
        string='Asignaturas Online (Texto)',
        help=_("Listado de asignaturas online (separadas por línea) para imprimir en el diplomado.")
    )
