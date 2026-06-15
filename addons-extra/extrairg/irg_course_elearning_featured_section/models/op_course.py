# -*- coding: utf-8 -*-

from odoo import fields, models


class OpCourse(models.Model):
    _inherit = 'op.course'

    irg_featured_section_enabled = fields.Boolean(
        string='Mostrar destacado en eLearning',
        help='Si está activo, se mostrará este bloque al inicio de las asignaturas eLearning vinculadas al curso.',
    )
    irg_featured_section_title = fields.Char(
        string='Título del destacado',
        translate=True,
    )
    irg_featured_section_body = fields.Html(
        string='Contenido del destacado',
        sanitize=True,
        translate=True,
    )
    irg_featured_section_embed_code = fields.Text(
        string='Código embebido',
        help='Código HTML de inserción opcional, por ejemplo un iframe. Solo debe configurarlo personal de confianza.',
    )
    irg_featured_section_url = fields.Char(
        string='URL del botón',
        help='Enlace opcional para el botón del bloque destacado.',
    )
    irg_featured_section_button_label = fields.Char(
        string='Texto del botón',
        translate=True,
        default='Ver más',
    )
