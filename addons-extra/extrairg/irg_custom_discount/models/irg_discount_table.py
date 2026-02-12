# -*- coding: utf-8 -*-
from odoo import models, fields


class IrgDiscountTable(models.Model):
    _name = 'irg.discount.table'
    _description = 'Tabla de Tarifas IRG'
    _order = 'name, id'

    name = fields.Char(string='Nombre', required=True)
    year = fields.Integer(string='Año')
    active = fields.Boolean(string='Activa', default=True)
    note = fields.Text(string='Notas')
    line_ids = fields.One2many('irg.discount.table.line', 'table_id', string='Líneas')


class IrgDiscountTableLine(models.Model):
    _name = 'irg.discount.table.line'
    _description = 'Línea de Tabla de Tarifas IRG'
    _order = 'table_id, sequence, id'

    sequence = fields.Integer(string='Secuencia', default=10)
    table_id = fields.Many2one('irg.discount.table', string='Tabla', required=True, ondelete='cascade')

    category_code = fields.Selection(
        [
            ('NC', 'NC'),
            ('PC', 'PC'),
            ('SC', 'SC'),
            ('DA', 'DA'),
            ('ND', 'ND'),
            ('PI', 'PI'),
            ('NL', 'NL'),
        ],
        string='Categoría',
        required=True,
    )
    modality = fields.Selection(
        [
            ('online', 'ONLINE'),
            ('homeclass', 'HOMECLASS'),
        ],
        string='Modalidad',
        required=True,
    )
    months = fields.Integer(string='Meses', required=True)

    installment_amount = fields.Float(string='Cuota')
    total_amount = fields.Float(string='Importe total')
    discount_percent = fields.Float(string='Descuento %')

    product_id = fields.Many2one('product.product', string='Producto relacionado')
