# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    @api.depends('admission_date')
    def _compute_period(self):
        for record in self:
            period = False
            if record.admission_date:
                term = self.env['op.academic.term'].search([
                    ('term_start_date', '<=', record.admission_date),
                    ('term_end_date', '>=', record.admission_date)
                ], limit=1)
                if term:
                    period = f"{term.academic_year_id.name}-{term.code}"
            record.period = period


    def gat_date_max_register(self, periodo):
        try:
            anio, nombre_termino = periodo.split("-", 1)
        except ValueError:
            raise ValueError("Formato de periodo inválido. Debe ser 'AÑO-NOMBRE_TERMINO'.")

        year = self.env['op.academic.year'].search([('name', '=', anio)], limit=1)
        if not year:
            raise ValueError(f"Año académico '{anio}' no encontrado.")

        term = self.env['op.academic.term'].search([
            ('academic_year_id', '=', year.id),
            ('code', '=', nombre_termino)
        ], limit=1)

        if not term:
            raise ValueError(f"Término '{nombre_termino}' no encontrado para el año {anio}.")

        return term.term_end_date
