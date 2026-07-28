# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.http import request


class PracticeRequest(models.Model):
    _inherit = 'practice.request'

    irg_preferred_quarter = fields.Selection(
        selection=[
            ('marzo_mayo', 'Marzo a Mayo'),
            ('junio_agosto', 'Junio a Agosto'),
            ('septiembre_noviembre', 'Septiembre a Noviembre'),
            ('diciembre_febrero', 'Diciembre a Febrero'),
        ],
        string='Trimestre preferente para iniciar las prácticas',
        help='Trimestre preferente seleccionado por el alumno para el inicio de sus prácticas',
    )

    @api.model_create_multi
    def create(self, vals_list):
        if request and getattr(request, 'httprequest', None) and request.httprequest.method == 'POST':
            quarter = (
                request.params.get('irg_preferred_quarter')
                or request.httprequest.form.get('irg_preferred_quarter')
            )
            if quarter:
                for vals in vals_list:
                    if not vals.get('irg_preferred_quarter'):
                        vals['irg_preferred_quarter'] = quarter
        return super().create(vals_list)
