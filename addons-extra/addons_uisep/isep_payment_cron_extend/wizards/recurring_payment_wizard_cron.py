# -*- coding: utf-8 -*-
import logging
from datetime import date, timedelta, datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from textwrap import dedent

_logger = logging.getLogger(__name__)


class RecurringPaymentWizardCron(models.TransientModel):
    _name = 'recurring.payment.wizard.cron'
    _description = _('Wizard: Cobro recurrente con porcentaje pendiente')


    pendiente = fields.Integer(string='Pendiente %', default=100,
                              help='Porcentaje')
    meses = fields.Integer(string='Meses', help='Número de meses para filtrar facturas vencidas', default=1)
    conpany_all = fields.Boolean(string='Todas las Compañías', default=False)
    note = fields.Text(string='Nota', readonly=True, 
        default=lambda self: dedent("""\
            # meses: cantidad de facturas con meses hacia atrás de vencimiento, se aplica al filtro
            # previsualizar: True o False, True para visualizar qué facturas intentará cobrar y False para cobrar
            # pendiente: valor en porcentaje; por defecto 100 para intentar el 100% de la deuda; puede ser 10, 20, 50, etc.
            # conpany_all: False respeta que el token sea de la misma empresa; True requerirá conciliación manual si el cobro tiene éxito.
        """))


    def _validate(self):
        self.ensure_one()
        if not self.pendiente or self.pendiente < 1 or self.pendiente > 100:
            raise UserError("El valor de 'pendiente' debe estar entre 1 y 100.")

    
    def _collect_invoices_to_process(self, meses=None, conpany_all=False):
        today = date.today()
        deadline = None
        if meses and isinstance(meses, int) and meses > 0:
            deadline = today - timedelta(days=meses * 30)

        sale_orders = self.env['sale.order'].search([
            ('state', 'in', ('sale', 'done')),
            ('stage_id.custom_cron', '=', True),
            ('payment_token_id', '!=', False),
        ])

        invoices_to_process = []
        for sale in sale_orders:
            payment_token = sale.payment_token_id
            company_token = payment_token.company_id

            if conpany_all:
                order_invoice_ids = sale.invoice_ids.filtered(
                    lambda inv: inv.state == 'posted' 
                        and inv.payment_state in ('not_paid', 'partial') 
                        and inv.move_type == 'out_invoice'
                )
            else:
                order_invoice_ids = sale.invoice_ids.filtered(
                    lambda inv: inv.state == 'posted' 
                        and inv.payment_state in ('not_paid', 'partial') 
                        and inv.move_type == 'out_invoice' 
                        and inv.company_id.id == company_token.id
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
                invoices_to_process.append((invoice_to_process.id, sale.id, payment_token.id))
        
        return invoices_to_process

    
    def action_previsualizar(self):
        self._validate()
        return self.env['payment.transaction']._cron_recurring_payment_sale_order(
            meses=int(self.meses) if self.meses else None,
            previsualizar=True,
            pendiente=int(self.pendiente),
            conpany_all=bool(self.conpany_all)
        )

    
    def action_ejecutar(self):
        self._validate()
        p = int(self.pendiente)
        meses = int(self.meses) if self.meses else None
        conpany_all = bool(self.conpany_all)

        if p == 100:
            msg = self.env['payment.transaction'].sudo()._cron_recurring_payment_sale_order(
                meses=meses,
                previsualizar=False,
                pendiente=100,
                conpany_all=conpany_all
            )
            if isinstance(msg, str):
                self.env.cr.commit()
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    "params": {
                        "title": "Cobros programados (100%)", 
                        "message": msg, 
                        "sticky": False, 
                        "type": "success"},
                } | {"type": "ir.actions.act_window_close"}
            return {"type": "ir.actions.act_window_close"}

        invoices_to_process = self._collect_invoices_to_process(meses=meses, conpany_all=conpany_all)
        if not invoices_to_process:
            raise UserError("No se encontraron órdenes/facturas pendientes de pago para procesar.")

        batch_size = 50
        total = len(invoices_to_process)
        for i in range(0, total, batch_size):
            batch = invoices_to_process[i:i + batch_size]
            batch_literal = "[" + ",".join(f"({inv},{so},{tok})" for inv, so, tok in batch) + "]"

            cron_code = f"model._process_invoice_batch({batch_literal}, {p})"

            delay_minutes = (i // batch_size) * 5
            exec_time = datetime.now() + timedelta(minutes=delay_minutes)

            self.env['ir.cron'].create({
                'name': f'Vista - Cobrador lote  ({p}%) {i // batch_size + 1}',
                'model_id': self.env['ir.model']._get_id('payment.transaction'),
                'state': 'code',
                'code': cron_code,
                'interval_type': 'minutes',
                'interval_number': 1,
                'numbercall': 1,
                'nextcall': exec_time.strftime('%Y-%m-%d %H:%M:%S'),
                'active': True,
            })
        msg = f"{total} facturas programadas en bloques de 50 para cobro único de {p}%."
        self.env.cr.commit()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Cobros programados (≠100%)", 
                "message": msg, 
                "sticky": False, 
                "type": "success"},
        } | {"type": "ir.actions.act_window_close"}






        

        
