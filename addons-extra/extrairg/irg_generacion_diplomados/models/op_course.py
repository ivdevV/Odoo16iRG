# -*- coding: utf-8 -*-

from odoo import models, fields, _

class OpCourse(models.Model):
    _inherit = 'op.course'

    irg_diplomado_subject_ids = fields.Many2many(
        'op.subject',
        'course_diplomado_subject_rel',
        'course_id',
        'subject_id',
        string='Asignaturas del Diplomado',
        help=_("Asignaturas predefinidas que figurarán en el diplomado para este curso.")
    )
