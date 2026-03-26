# -*- coding: utf-8 -*-
from odoo import models, fields


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    gradebook_subject_ids = fields.One2many(
        comodel_name='app.gradebook.subject',
        inverse_name='admission_id',
        string='Asignaturas',
    )
