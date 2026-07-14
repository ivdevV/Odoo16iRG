# -*- coding: utf-8 -*-

from odoo import fields, models


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    oficialidad_sent_date = fields.Datetime(
        string='Última oficialidad enviada',
        readonly=True,
        copy=False,
    )
