# -*- coding: utf-8 -*-
import logging
from datetime import date, timedelta, datetime, time
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'


    def _cron_recurring_payment_sale_order(self, meses=None, previsualizar=False, pendiente=False, conpany_all=False):
        if not pendiente or pendiente > 100:
            return

        sale_order = self.env['sale.order']
        today = date.today()

        domain = [
            ('state', 'in', ('sale', 'done')),
            ('stage_id.custom_cron', '=', True),
            ('payment_token_id', '!=', False),
        ]
        sale_orders = sale_order.search(domain)

        if not sale_orders:
            _logger.info("No se encontraron órdenes pendientes de pago para procesar.")
            return "No se encontraron órdenes pendientes de pago para procesar."

        deadline = None
        if meses and isinstance(meses, int) and meses > 0:
            deadline = today - timedelta(days=meses * 30)

        invoices_to_process = []

        for sale in sale_orders:
            payment_token = sale.payment_token_id
            company_token = payment_token.company_id

            if conpany_all:
                order_invoice_ids = sale.invoice_ids.filtered(
                    lambda inv: inv.state == 'posted' and
                                inv.payment_state in ('not_paid', 'partial') and
                                inv.move_type == 'out_invoice'
                )
            else:
                order_invoice_ids = sale.invoice_ids.filtered(
                    lambda inv: inv.state == 'posted' and
                                inv.payment_state in ('not_paid', 'partial') and
                                inv.move_type == 'out_invoice' and
                                inv.company_id.id == company_token.id
                )

            invoice_to_process = False
            for invoice in order_invoice_ids.sorted(key=lambda inv: inv.invoice_date_due):
                if deadline and invoice.invoice_date_due < deadline:
                    continue
                if invoice.invoice_date_due > today:
                    continue
                invoice_to_process = invoice
                break

            if invoice_to_process:
                retry_exists = self.env['payment.retry.log'].search_count([
                    ('invoice_id', 'in', sale.invoice_ids.ids),
                    ('state', '=', 'pending'),
                ])
                if retry_exists:                    
                    continue

                invoices_to_process.append((invoice_to_process.id, sale.id, payment_token.id))

        
        if previsualizar:
            if not invoices_to_process:
                raise UserError("No hay facturas válidas para procesar.")

            COP = self.env.ref('base.COP').id
            result_lines = []
            for invoice_id, sale_id, token_id in invoices_to_process:
                invoice = self.env['account.move'].browse(invoice_id)
                factor = pendiente * 0.01
                amount_residual = invoice.amount_residual
                if pendiente != 100:
                    amount_residual = round(amount_residual * factor, 2)
                if invoice.currency_id.id == COP and amount_residual > 999999:
                    amount_residual = 999999
                result_lines.append(
                    f"ID: {invoice.id}, Factura: {invoice.name}, Fecha: {invoice.invoice_date}, Fecha vencimiento: {invoice.invoice_date_due}, "
                    f"Cliente: {invoice.partner_id.name}, Pendiente de pago: {amount_residual}, Moneda: {invoice.currency_id.name}"
                )
            raise UserError("Facturas a procesar:\n" + "\n".join(result_lines))

        batch_size = 50
        for i in range(0, len(invoices_to_process), batch_size):
            batch = invoices_to_process[i:i + batch_size]
            delay_minutes = (i // batch_size) * 5
            exec_time = datetime.now() + timedelta(minutes=delay_minutes)
            self.env['ir.cron'].create({
                'name': f'Cobrador lote {i // batch_size + 1}',
                'model_id': self.env['ir.model']._get_id('payment.transaction'),
                'state': 'code',
                'code': f"model._process_invoice_batch({batch}, {pendiente})",
                'interval_type': 'minutes',
                'interval_number': 1,
                'numbercall': 1,
                'nextcall': exec_time.strftime('%Y-%m-%d %H:%M:%S'),
                'active': True,
            })

        return f"{len(invoices_to_process)} facturas programadas para cobro segmentado."


    @api.model
    def _process_invoice_batch(self, batch, pendiente):
        for invoice_id, sale_id, token_id in batch:
            invoice = self.env['account.move'].browse(invoice_id)
            sale = self.env['sale.order'].browse(sale_id)
            token = self.env['payment.token'].browse(token_id)

            try:
                # Intento 1: 100%
                result = self._send_build_payment_request(invoice, sale, token, pendiente)
                if result['success']:
                    _logger.info(f"[OK] Pago completo 100% para factura {invoice.name}")
                    continue

                # Revisar si es por fondos insuficientes
                error_msg = result.get('error_message', '')
                if 'insufficient funds' in error_msg.lower():
                    _logger.warning(f"[REINTENTO] Fondos insuficientes, intentando 25% → 50% + 25% para {invoice.name}")

                    # Intento 2: 25%
                    result_25 = self._send_build_payment_request(invoice, sale, token, 25)
                    if not result_25['success']:
                        _logger.warning(f"[STOP] Falló 25%, se detiene en {invoice.name}")
                        continue

                    # Intento 3: 50%
                    result_50 = self._send_build_payment_request(invoice, sale, token, 50)
                    if result_50['success']:
                        # Intento 4: otro 25%
                        self._send_build_payment_request(invoice, sale, token, 25)
                    else:
                        _logger.warning(f"[PARCIAL] 50% OK, pero falló el segundo  25% en {invoice.name}")

                elif 'was declined' in error_msg.lower() or 'has expired' in error_msg.lower():
                    retry_date = fields.Date.today()
                    self.env['payment.retry.log'].create({
                        'invoice_id': invoice.id,
                        'sale_order_id': sale.id,
                        'token_id': token.id,
                        'retry_date': retry_date,
                        'attempt_percent': pendiente,
                        'error_message': error_msg,
                        'reference': f'{sale.name}:{invoice.name}',
                    })
                    _logger.warning(f"[REINTENTO DIFERIDO] Factura {invoice.name} agendada para reintento en {retry_date}")
                    continue
                else:
                    _logger.info(f"[NO RETRY] Error diferente para {invoice.name} {invoice.name}: {error_msg}")

            except Exception as e:
                _logger.error(f"[ERROR GENERAL] {invoice.name}: {str(e)}")


    def _send_build_payment_request(self, invoice, order, payment_token, pendiente):
        if not pendiente or pendiente > 100:
            return {'success': False, 'error_message': 'Porcentaje inválido'}

        factor = pendiente * 0.01
        current_time = datetime.now()
        time_cron = current_time.strftime("%H:%M:%S.%f")[:-2]
        COP = self.env.ref('base.COP').id
        amount_residual = invoice.amount_residual

        if pendiente != 100:
            amount_residual = round(amount_residual * factor, 2)

        if invoice.currency_id.id == COP and amount_residual > 999999:
            amount_residual = 999999

        try:
            transaction = self.env['payment.transaction'].create({
                'amount': amount_residual,
                'currency_id': invoice.currency_id.id,
                'partner_id': invoice.partner_id.id,
                'token_id': payment_token.id,
                'invoice_ids': [(6, 0, [invoice.id])],
                'provider_id': payment_token.provider_id.id,
                'operation': 'online_token',
                'reference': f'{order.name}:{invoice.name}-{time_cron}',
                'callback_method': 'reconcile_pending_transaction',
                'custom_cron': True,
            })

            self.env.cr.commit()
            transaction._send_payment_request()
            self.env.cr.commit()

            if transaction.state == 'done':
                return {'success': True}
            else:
                return {
                    'success': False,
                    'error_message': transaction.state_message
                }

        except Exception as e:
            self.env.cr.rollback()
            return {'success': False, 'error_message': f'Excepción: {str(e)}'} 