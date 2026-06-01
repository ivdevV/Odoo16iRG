# -*- coding: utf-8 -*-
from odoo import fields, models


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    irg_class_start_date = fields.Date(
        string='Fecha de inicio de clases',
        copy=False,
    )
