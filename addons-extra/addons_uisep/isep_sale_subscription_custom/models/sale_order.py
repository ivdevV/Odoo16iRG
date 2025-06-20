import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime
import pytz


_logger = logging.getLogger(__name__)



class SaleOrder(models.Model):
    _inherit = 'sale.order'

    recurring_rule_count = fields.Integer(string="Número de pagos", default=1)
    sale_note_inv = fields.One2many('sale.note.inv', 'order_id', string='Registros Anteriores')
    amount_no_recurring_taxinc = fields.Monetary(compute='_compute_amount_recurring_taxinc', string="Importe no recurrente", store=True)    
    amount_recurring_taxinc = fields.Monetary(compute='_compute_amount_recurring_taxinc', string="Importe recurrente", store=True)
    amount_total_recurring = fields.Monetary(compute='_compute_amount_total_recurring', string="Total recurrente", store=True)
    amount_total_sale = fields.Monetary(compute='_compute_amount_total_recurring', string="Importe total", store=True, help="Importe recurrente total + Importe no recurrente" )
    
    amount_total_invoice = fields.Monetary(compute='_compute_amount_total_invoice', string="Total Facturado", store=True)
    amount_total_payment = fields.Monetary(compute='_compute_amount_total_invoice', string="Total Pagado", store=True)
    current_recurring_period = fields.Integer(string="Período recurrente actual", compute='compute_current_recurring_period', store=True)
    current_recurring_period_string = fields.Char(string="Período actual", compute='compute_current_recurring_period', store=True)
    amount_recurring_to_date = fields.Monetary(compute='_compute_amount_recurring_due', string="Total Ideal actual", store=True, help="Representa el total facturado y pagado ideal")
    amount_recurring_due = fields.Monetary(compute='_compute_amount_recurring_due', string="Total Vencido", store=True)

    last_payment_date = fields.Date(compute='_compute_amount_total_invoice', string="Ultima fecha de pago", store=True)
    
    @api.depends('amount_no_recurring_taxinc','amount_recurring_taxinc','current_recurring_period','amount_total_payment')
    def _compute_amount_recurring_due(self):
        for rec in self:
            amount_recurring_to_date = (rec.amount_no_recurring_taxinc+(rec.amount_recurring_taxinc*rec.current_recurring_period))
            amount_recurring_due = amount_recurring_to_date - rec.amount_total_payment            
            if amount_recurring_due < 0.0:
                amount_recurring_due = 0.0
            rec.amount_recurring_due = amount_recurring_due
            rec.amount_recurring_to_date = amount_recurring_to_date

    @api.onchange('recurring_rule_count')
    def onchange_recurring_rule_count(self):
        for rec in self:
            if rec.recurring_rule_count > 120:
                raise UserError('El campo "Número de pagos" se encuentra controlado, el número máximo actual es 120.')

            if rec.recurring_rule_count < 0:
                raise UserError('El campo "Número de pagos" no puede ser un valor negativo.')

    def cron_compute_current_recurring_period(self):        
        suscrip = self.env['sale.order'].search([('recurrence_id','!=', False),('state','in', ('sale','done') ),('stage_id.category','=', 'progress')])
        for line in suscrip:
            line.compute_current_recurring_period()

    @api.depends('start_date','recurring_rule_count','recurrence_id')
    def compute_current_recurring_period(self):
        for rec in self:
            current_recurring_period = 0
            current_recurring_period_string = '%s / %s' % (str(current_recurring_period).zfill(2),str(rec.recurring_rule_count).zfill(2))
            if rec.start_date and rec.recurrence_id:                
                duration = rec.recurrence_id.duration
                unit = rec.recurrence_id.unit # day, week, month,year
                period = relativedelta(day=0)
                for i in range(1,rec.recurring_rule_count+1):
                    tz = pytz.timezone('America/Mexico_City')
                    current_date = datetime.now(tz).date()
                    if  unit == 'month':
                        period=relativedelta(months=duration*i)
                    elif unit == 'day':
                        period=relativedelta(days=duration*i)
                    elif unit == 'week':
                        period=relativedelta(weeks=duration*i)
                    elif unit == 'year':
                        period=relativedelta(years=duration*i)                    
                    current_recurring_period = i
                    if current_date < rec.start_date+period:   
                        break
                current_recurring_period_string = '%s / %s' % (str(current_recurring_period).zfill(2),str(rec.recurring_rule_count).zfill(2))            
            rec.current_recurring_period = current_recurring_period
            rec.current_recurring_period_string = current_recurring_period_string

    @api.depends('invoice_ids','invoice_ids.state','invoice_ids.invoice_payments_widget','sale_note_inv.amount_total_payment','sale_note_inv.amount_total_invoice')
    def _compute_amount_total_invoice(self):
        for rec in self:
            amount_total_invoice = 0.0
            amount_total_payment = 0.0
            last_payment_date = False
            if rec.state in ("sale","done") and rec.invoice_ids:                
                for invoice in rec.invoice_ids:
                    if invoice.state in ("posted"):
                        amount_total_invoice += invoice.amount_total_in_currency_signed
                        if invoice.invoice_payments_widget:
                            for payment in invoice.invoice_payments_widget['content']:
                                amount_total_payment += payment['amount']
                                if last_payment_date == False:
                                    last_payment_date = payment['date']
                                if last_payment_date < payment['date']:
                                    last_payment_date = payment['date']
            
            rec.amount_total_invoice = amount_total_invoice+sum(rec.sale_note_inv.mapped('amount_total_invoice'))
            rec.amount_total_payment = amount_total_payment+sum(rec.sale_note_inv.mapped('amount_total_payment'))            
            rec.last_payment_date = last_payment_date
            #update



    """
    invoice_payments_widget
    {   'title': 'Menos pagos', 'outstanding': False, 
        'content': [{   'name': 'Pago de cliente $\xa02,000.00 - JUAN MENDEZ OLIVARES - 11/12/2023', 
                        'journal_name': 'Banco', 
                        'amount': 2000.0, 
                        'currency_id': 33, 
                        'date': datetime.date(2023, 12, 11), 
                        'partial_id': 4, 
                        'account_payment_id': 2, 
                        'payment_method_name': 'Manual', 
                        'move_id': 25, 
                        'ref': 'PBNK1/2023/00001 (INV/2023/00014)', 
                        'is_exchange': False, 
                        'amount_company_currency': '$\xa02,000.00', 
                        'amount_foreign_currency': False}, 
        ]}
    """
    
    @api.depends('recurring_rule_count', 'amount_recurring_taxinc')
    def _compute_amount_total_recurring(self):
        for order in self:
            order.amount_total_recurring = order.amount_recurring_taxinc*order.recurring_rule_count
            order.amount_total_sale = order.amount_total_recurring + order.amount_no_recurring_taxinc

    @api.depends('is_subscription', 'amount_untaxed')
    def _compute_amount_recurring_taxinc(self):
        for order in self:
            amount_recurring_taxinc = 0.0
            amount_no_recurring_taxinc = 0.0
            if order.is_subscription or order.order_line:
                amount_recurring_taxinc = sum(order.order_line.filtered(lambda x: x.product_template_id.recurring_invoice == True).mapped('price_reduce_taxinc'))
                amount_no_recurring_taxinc = sum(order.order_line.filtered(lambda x: x.product_template_id.recurring_invoice == False).mapped('price_reduce_taxinc'))
            order.amount_recurring_taxinc = amount_recurring_taxinc
            order.amount_no_recurring_taxinc = amount_no_recurring_taxinc

    

    @api.onchange('recurring_rule_count','recurrence_id','start_date')
    def onchange_end_date_suscrip(self):
        for sub in self:
            if sub.start_date and sub.recurrence_id:
                period = relativedelta(day=0)
                duration = sub.recurrence_id.duration*sub.recurring_rule_count
                unit = sub.recurrence_id.unit # day, week, month,year
                if  unit == 'month':
                    period=relativedelta(months=duration)
                elif unit == 'day':
                    period=relativedelta(days=duration)
                elif unit == 'week':
                    period=relativedelta(weeks=duration)
                elif unit == 'year':
                    period=relativedelta(years=duration)
                end_date = sub.start_date + period - relativedelta(days=1)
                sub.write({'end_date': end_date})
                sub.order_line._reset_subscription_qty_to_invoice()

