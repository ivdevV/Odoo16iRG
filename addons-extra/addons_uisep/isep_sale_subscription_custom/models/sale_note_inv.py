import logging
from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)



class SaleNoteInv(models.Model):
    _name = 'sale.note.inv'
    _description = 'Informacion de facturas de Odoo 12' 

    name = fields.Char(string="Referencia")
    order_id = fields.Many2one('sale.order', string="Venta", ondelete='cascade' )
    note = fields.Text(string="Nota")
    currency_id = fields.Many2one('res.currency', related="order_id.currency_id", string="Moneda")
    type = fields.Selection([
        ('invoice', 'Factura'),
        ('others', 'Otros'),
        ], required=True, default="invoice", string="Tipo")
    amount_total_payment = fields.Monetary(string="Total Pagado")
    amount_total_invoice = fields.Monetary(string="Total Facturado")
