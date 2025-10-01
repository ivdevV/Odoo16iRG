# -*- coding: utf-8 -*-
import logging
from datetime import date, timedelta, datetime, time
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PaymentRetryLog(models.Model):
    _name = 'payment.retry.log'
    _description = 'PaymentRetryLog'
    _name_search_order = 'id desc'


    name = fields.Char(string='Nombre', readonly=True, copy=False, default='Nuevo')
    invoice_id = fields.Many2one('account.move', ondelete='cascade', string='Factura')
    sale_order_id = fields.Many2one('sale.order', ondelete='cascade', string='Pedido de Venta')
    token_id = fields.Many2one('payment.token', ondelete='cascade', string='Token de Pago')
    provider_id = fields.Many2one('payment.provider', related='token_id.provider_id', store=True, string='Proveedor')
    retry_date = fields.Date(string='Fecha de Reintento')
    attempt_percent = fields.Float(string='Porcentaje', default=100.0)
    state = fields.Selection([
        ('pending', 'Pendiente')
    ], default='pending', string='Estado')
    error_message = fields.Text(string='Mensaje de Error')
    reference = fields.Char(string='Referencia de Transacción')


    @api.model
    def create(self, vals):
        if not vals.get('name'):
            invoice = self.env['account.move'].browse(vals.get('invoice_id'))
            vals['name'] = f"Reintento - {invoice.name or 'Factura desconocida'}"
        return super().create(vals)

    
    @api.model
    def _cron_clean_old_logs(self, days=30, previsualizar=False):
        today = fields.Date.today()
        target_date = today - timedelta(days=days)
        start_of_target_day = datetime.combine(target_date, time.min)
        end_of_target_day = datetime.combine(target_date, time.max)
        logs = self.search([
            ('state', '=', 'pending'),
            ('retry_date', '>=', start_of_target_day),
            ('retry_date', '<=', end_of_target_day),
        ])
        count = len(logs)

        if previsualizar:
            if not logs:
                raise UserError("No hay registros antiguos para eliminar.")
            lines = [
                f"{r.name or r.reference or 'Sin referencia'} | Estado: {r.state} | Fecha de reintento: {r.retry_date}"
                for r in logs
            ]
            raise UserError(
                "Registros que serían eliminados:\n" + "\n".join(lines)
            )

        logs.unlink()


