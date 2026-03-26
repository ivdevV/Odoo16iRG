# -*- coding: utf-8 -*-
from odoo import models, fields


class OpAdmission(models.Model):
    _inherit = 'op.admission'

    # One2many to gradebook subjects via the stored admission_id field
    # on app.gradebook.subject (which is a related stored field from
    # app.gradebook.student.admission_id).
    gradebook_subject_ids = fields.One2many(
        comodel_name='app.gradebook.subject',
        inverse_name='admission_id',
        string='Asignaturas',
    )
