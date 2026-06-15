# -*- coding: utf-8 -*-

from odoo import models, fields, _

class OpSubject(models.Model):
    _inherit = 'op.subject'

    irg_modality = fields.Selection([
        ('presencial', 'Presencial'),
        ('online', 'Online')
    ], string='Modalidad', default='online', help=_("Modalidad de la asignatura para clasificar en el diplomado."))

    course_ids = fields.Many2many(
        'op.course',
        relation='op_course_op_subject_rel',
        column1='op_subject_id',
        column2='op_course_id',
        string='Cursos',
        help=_("Cursos que contienen esta asignatura.")
    )

