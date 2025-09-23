# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderAdmissionLine(models.Model):
    _name = 'sale.order.admission.line'
    _description = 'Relación de admisiones en el pedido de venta'

    order_id = fields.Many2one('sale.order', string='Pedido', ondelete='cascade', required=True, index=True, copy=False)
    sale_line_id = fields.Many2one('sale.order.line', string='Línea de venta', ondelete='set null', index=True, copy=False)
    admission_register_id = fields.Many2one('op.admission.register', string='Registro de Admision', copy=False)
    admission_id = fields.Many2one('op.admission', string="Admisión" , copy=False )
    admission_date = fields.Date(string="Fecha de Inicio",  copy=False )
    period = fields.Char(string="Periodo de Admisión", compute="_compute_period", store=True,  copy=False)
    error_admission = fields.Boolean(string="Error en el proceso",  copy=False )
    error_admission_msn = fields.Html(string="Error en el proceso, detalle",  copy=False )
    product_template_id = fields.Many2one('product.template', string="Producto",  copy=False)
    course_id = fields.Many2one('op.course', string="Curso",  copy=False)

    _sql_constraints = [
        (
            'uniq_order_sale_line', 
            'unique(order_id, sale_line_id)',
            'Ya existe una fila de admisión para esta línea en este pedido.')
        ]


    @api.depends('admission_date')
    def _compute_period(self):
        for rec in self:
            period = False
            if rec.admission_date:
                year = rec.admission_date.year
                month = rec.admission_date.month
                if month in (1, 2, 3, 4):
                    period = f'{year}-01'
                elif month in (5, 6, 7):
                    period = f'{year}-02'
                else:
                    period = f'{year}-03'
            rec.period = period