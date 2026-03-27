# -*- coding: utf-8 -*-
from odoo import models, fields


class OpStudent(models.Model):
    _inherit = 'op.student'

    # Override: remove the compute to make op_admission_ids a standard
    # One2many. The original isep_student_filter defines it as
    # compute='_compute_admissions' (no inverse), which forces the entire
    # field — and every nested sub-record — to be readonly in the UI.
    # Since op.admission already has a stored student_id Many2one,
    # a regular One2many works identically for reading and also allows writes.
    op_admission_ids = fields.One2many(
        'op.admission',
        'student_id',
        string='Admisión',
    )
