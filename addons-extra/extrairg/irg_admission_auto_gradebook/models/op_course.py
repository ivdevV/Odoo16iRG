# -*- coding: utf-8 -*-
from odoo import fields, models


class OpCourse(models.Model):
    _inherit = 'op.course'

    auto_create_gradebook = fields.Boolean(
        string='Crear libreta automáticamente',
        default=True,
        help=(
            'Si está activo, se creará automáticamente la libreta de '
            'calificaciones al confirmar la matrícula (Enroll Student).'
        ),
    )
    auto_gradebook_subject_filter = fields.Selection(
        string='Asignaturas a incluir en la libreta',
        selection=[
            ('compulsory', 'Solo obligatorias'),
            ('all', 'Todas (obligatorias + electivas)'),
        ],
        default='compulsory',
        help=(
            'Determina qué asignaturas del curso se añaden automáticamente '
            'a la libreta al confirmar la matrícula.'
        ),
    )
