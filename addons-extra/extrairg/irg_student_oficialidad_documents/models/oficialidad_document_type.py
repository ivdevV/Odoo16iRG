# -*- coding: utf-8 -*-
from odoo import api, fields, models


class IrgOficialidadDocumentType(models.Model):
    _name = 'irg.oficialidad.document.type'
    _description = 'Tipo de documento de oficialidad IRG'
    _order = 'id'

    key = fields.Char(required=True, index=True)
    name = fields.Char(required=True, translate=True)
    student_type_scope = fields.Selection(
        selection=[
            ('nacional', 'Nacional'),
            ('internacional', 'Internacional'),
            ('both', 'Ambos'),
        ],
        required=True,
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('key_uniq', 'unique(key)', 'La clave del tipo de documento debe ser unica.'),
    ]

    @api.model
    def get_expected_keys(self, student_type):
        if student_type not in ('nacional', 'internacional'):
            return []
        types = self.search([
            ('active', '=', True),
            ('student_type_scope', 'in', [student_type, 'both']),
        ])
        # Stable order matching the app README tables
        order = {
            'nacional': [
                'titulo-universitario',
                'certificado-notas',
                'matricula-unimarconi',
                'documento-identificativo-nacional',
            ],
            'internacional': [
                'titulo-universitario-apostillado',
                'apostilla-certificado-notas',
                'matricula-unimarconi',
                'pasaporte',
            ],
        }[student_type]
        by_key = {rec.key: rec for rec in types}
        return [key for key in order if key in by_key]
