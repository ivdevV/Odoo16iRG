# -*- coding: utf-8 -*-
from odoo import models, fields


class AutoAdmissionRequired(models.Model):
    _inherit = 'auto.admission.required'

    quarterly_online_enabled = fields.Boolean(
        string="Activar convocatorias trimestrales Online",
        default=True,
        help="Si esta activo, los lotes de modalidad Online (ONL) se agrupan "
             "por trimestre (A/B/C/D) en vez de generarse uno mensual.",
    )
