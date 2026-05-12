# -*- coding: utf-8 -*-

from odoo import fields, models


class IrgDiplomaRegistry(models.Model):
    _inherit = 'irg.diploma.registry'

    verification_code = fields.Char(
        string='Código de Verificación QR',
        index=True,
        copy=False,
        help='Código corto usado en la URL del QR, por ejemplo DAN-5026.',
    )

    _sql_constraints = [
        (
            'unique_verification_code',
            'unique(verification_code)',
            'El código de verificación QR ya existe.',
        ),
    ]
