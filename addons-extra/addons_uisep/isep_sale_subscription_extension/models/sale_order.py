import logging
from odoo import models, fields, api
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from datetime import datetime
from psycopg2.extensions import TransactionRollbackError
from odoo.tools import html_escape
import pytz
from odoo.tools import config
import re

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # ... (I will copy the content here)
    # For now I'll just put the structure and then use insert_edit_into_file or replace_string_in_file to fill it
    # Actually I have the content in memory from the previous read_file.
    
    subscription_schedule = fields.One2many('sale.subscription.schedule', 'order_id', string='Cronograma de pagos')
    term_number_id = fields.Many2one('product.term.schedule', string='Plan de Suscripción' )
    term_number = fields.Integer('Nro. Plazos')
    term_custom = fields.Boolean(string="Es personalizado", related="term_number_id.custom")
    
    amount_due_total = fields.Monetary(
        string='Importe total vencido',
        compute='_compute_amount_due_total',
        store=True,
        currency_field='currency_id'
    )

    due_line_ids = fields.Many2many(
        comodel_name='sale.subscription.schedule',
        inverse_name='order_id',
        string='Vencimientos sin pagar',
        compute='_compute_due_line_ids',store=True
    )

    total_paid = fields.Float(
        string='Total pagado',
        compute='_compute_total_paid',
        store=False,
        currency_field='currency_id'
    )
    total_recurring = fields.Float(
        string='Total a pagar',
        compute='_compute_amount_recurring',
        store=False,
        currency_field='currency_id'
    )

    @api.depends('subscription_schedule.total_paid', 'subscription_schedule.payment_state')
    def _compute_total_paid(self):  
        for order in self:
            total_paid = 0.0
            for sched in order.subscription_schedule:
                total_paid += sched.total_paid
            order.total_paid = total_paid

    @api.depends('subscription_schedule.amount_recurring_taxinc','subscription_schedule.payment_state')
    def _compute_amount_recurring(self):
        for order in self:
            total_residual = 0.0
            for sched in order.subscription_schedule:
                total_residual += sched.amount_recurring_taxinc
            order.total_recurring = total_residual

    @api.depends('subscription_schedule.date_due', 'subscription_schedule.payment_state')
    def _compute_due_line_ids(self):
        today = fields.Date.today()
        for order in self:
            order.due_line_ids = order.subscription_schedule.filtered(
                lambda l: l.date_due and l.date_due < today and l.payment_state == 'not_paid'
            )

    @api.depends('invoice_ids.amount_residual', 'invoice_ids.state')
    def _compute_amount_due_total(self):
        for order in self:
            amount_due_total = 0.0
            for invoice in order.invoice_ids:
                if invoice.state == 'posted':
                    amount_due_total += invoice.amount_residual
            order.amount_due_total = amount_due_total

    def _auto_scheduled_order(self):
        _logger.info("--- START _auto_scheduled_order for order %s ---", self.name)
        list_product_comb = []
        # Usamos nombres distintos para el modelo y el registro para evitar confusiones
        TermSchedule = self.env['product.term.schedule'].sudo()
        PaymentTerm = self.env['account.payment.term'].sudo()
        
        # Variable para almacenar la duración del curso si no hay atributos
        course_duration = 0

        for ol in self.order_line:
            _logger.info("Processing line: %s (Recurring: %s)", ol.product_id.name, ol.product_id.recurring_invoice)
            if ol.product_id.recurring_invoice:
                # Intento 1: Atributos (Planes)
                if ol.product_id.product_template_attribute_value_ids:
                    for ptav in ol.product_id.product_template_attribute_value_ids:
                        _logger.info("Attribute found: %s (ID: %s, Name: %s)", ptav.attribute_id.name, ptav.attribute_id.id, ptav.name)
                        # Buscamos por nombre o si tiene un 'plazo' definido
                        if ptav.attribute_id.name == 'Planes':
                            list_product_comb.append(ptav.id)
                            break
                        
                elif ol.product_id.combination_indices:
                    # ... (Tu lógica de combinación indices se mantiene igual) ...
                    combination_str = str(ol.product_id.combination_indices)
                    if ',' in combination_str:
                        first_id = combination_str.split(',')[0].strip()
                        try:
                            list_product_comb.append(int(first_id))
                        except ValueError:
                            _logger.warning("No se pudo convertir combination_indices: %s", first_id)
                    else:
                        try:
                            list_product_comb.append(int(combination_str))
                        except ValueError:
                            pass # Ignoramos errores silenciosamente
                
                # Intento 3: Duración del curso (Fallback si no hay atributos)
                if not list_product_comb:
                     # Buscar curso vinculado (Soporte para M2O y M2M si existe)
                     courses = False
                     if hasattr(ol.product_id.product_tmpl_id, 'product_template_ids'):
                         courses = ol.product_id.product_tmpl_id.product_template_ids
                     
                     if not courses and hasattr(ol.product_id.product_tmpl_id, 'course_id'):
                         courses = ol.product_id.product_tmpl_id.course_id
                     
                     if courses:
                         for course in courses:
                             # Asumimos que duration es un float/int representando meses o la unidad configurada
                             if course.duration > course_duration:
                                 course_duration = course.duration
        
        _logger.info("Course Duration Fallback: %s", course_duration)

        max_plazo = 0
        if list_product_comb:
            attribute = self.env['product.template.attribute.value'].sudo().search([('id', 'in', list_product_comb)])
            max_plazo = max(attribute.mapped('plazo')) if attribute.mapped('plazo') else 0
            
            # Lógica de rescate por nombre
            if max_plazo == 0:
                max_plazo_str = attribute.mapped('name')
                max_plazo_str = ','.join(max_plazo_str)                    
                coincidencias = re.findall(r'\d+', max_plazo_str)
                if coincidencias:
                    plazos = [int(num) for num in coincidencias]
                    max_plazo = max(plazos)
        
        _logger.info("Max Plazo from Attributes: %s", max_plazo)

        # Si no sacamos plazo de los atributos, usamos la duración del curso
        if max_plazo == 0 and course_duration > 0:
            max_plazo = int(course_duration)
            _logger.info("Using Course Duration as Max Plazo: %s", max_plazo)

        if max_plazo > 0:
            term_number_record = TermSchedule.search([('term_number', '=', max_plazo)], limit=1)
            if not term_number_record:
                 term_number_record = TermSchedule.search([('custom','=',True)], limit=1)
            
            term_number_id = term_number_record.id if term_number_record else False

            # Búsqueda de Términos de Pago Estricta
            payment_term_record = False
            
            # 1. Búsqueda Exacta (Insensible a mayúsculas): "3 Meses", "3 meses"
            # Usamos =ilike para que sea exacto pero no importe si escribieron "meses" o "Meses"
            payment_term_name = f'{max_plazo} Meses'
            payment_term_record = PaymentTerm.search([('name', '=ilike', payment_term_name)], limit=1)
            _logger.info("Search 1 '%s': Found %s", payment_term_name, payment_term_record.name if payment_term_record else 'None')
            
            # 2. Búsqueda con Cero a la Izquierda (Insensible a mayúsculas): "03 Meses", "03 meses"
            if not payment_term_record:
                 payment_term_name_02 = f'{max_plazo:02d} Meses'
                 payment_term_record = PaymentTerm.search([('name', '=ilike', payment_term_name_02)], limit=1)
                 _logger.info("Search 2 '%s': Found %s", payment_term_name_02, payment_term_record.name if payment_term_record else 'None')

            # NOTA: Se ha eliminado la búsqueda parcial ('ilike') para evitar que seleccione
            # términos como "15 Meses día 1" o "15 Meses matrícula" cuando buscamos solo "15 Meses".

            payment_term_id = payment_term_record.id if payment_term_record else False
            
            # Escritura
            vals = {
                'term_number_id': term_number_id,
                'term_number': max_plazo,
            }
            # Solo escribimos el plazo de pago si lo encontramos, para no borrar uno manual si existía
            if payment_term_id:
                vals['payment_term_id'] = payment_term_id
                
            self.write(vals)
            
            _logger.info("Autoschedule FINAL: Plazos=%s, PaymentTerm=%s (ID: %s)", max_plazo, payment_term_record.name if payment_term_record else 'No encontrado', payment_term_id)

            self.onchange_end_date_suscrip()
            self.create_subscription_schedule()
            
                    
    @api.onchange('term_number','recurrence_id','start_date')
    def onchange_end_date_suscrip(self):
        for sub in self:
            if sub.start_date and sub.recurrence_id:
                period = relativedelta(day=0)
                duration = sub.recurrence_id.duration*sub.term_number
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


    @api.onchange('term_number_id')
    def onchange_term_number(self):
        for record in self:
            if record.term_number_id and not record.term_number_id.custom:
                record.term_number = record.term_number_id.term_number
            if record.term_number_id and record.term_number_id.custom:
                value = record.term_number_id.term_number
                record.term_number = record.term_number if record.term_number > 0 else value
                
   

    def open_expand_view_tree_term(self):
        self.ensure_one()
        result = self.env['ir.actions.act_window']._for_xml_id('isep_sale_subscription_extension.sale_subscription_schedule_action')
        result['views'] = [(self.env.ref('isep_sale_subscription_extension.sale_subscription_schedule_view_tree', False).id, 'tree')]
        result['domain'] = [('id', 'in', self.subscription_schedule.ids)]
        # result['target'] = 'new'
        return result

    def term_number_value(self):
        term_number_id = False
        term_number = 0
        order_line = self.order_line.filtered(lambda x: x.product_id.subscription_plan != False)
        if order_line:
            for line in order_line:
                line_term_number = line.product_id.subscription_plan.term_number
                if term_number < line_term_number:
                    term_number = line_term_number
                    term_number_id = line.product_id.subscription_plan.id
        
        self.term_number_id = term_number_id

    def wizard_update_date_due(self):
        model_date_due = self.env['schedule.date.due']
        wizard = model_date_due.create({
            'order_id': self.id,
            'end_date': self.end_date,
            'next_invoice_date': self.next_invoice_date,
            'new_end_date': self.end_date,
            'new_next_invoice_date': self.next_invoice_date,
            'recurrence_id':self.recurrence_id.id,
        })
        for sl in self.subscription_schedule.filtered(lambda x: x.payment_state != 'paid'):
            self.env['schedule.date.due.line'].create({
                'schedule_date_due_id':wizard.id,
                'name':sl.id,
                'date_due': sl.date_due,
                'new_date_due':sl.date_due,
                'currency_id': sl.currency_id.id,
                'total_paid': sl.total_paid,
                'total_residual': sl.total_residual,
                'payment_state':sl.payment_state

            })

        return {
            'name': 'Prorogar fechas de vencimiento',
            'type': 'ir.actions.act_window',
            'res_model': 'schedule.date.due',
            'view_mode': 'form',
            'target': 'new',
            'flags': {'action_buttons': False},      
            'res_id': wizard.id
        }
    
    
    def view_search_all_invoice(self):
        self.ensure_one()
        invoice_ids = self.env['account.move'].search([('partner_id','in',(self.partner_invoice_id.id,self.partner_id.id ) )])
        result = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_invoice_type')
        result['views'] = [(self.env.ref('account.view_out_invoice_tree', False).id, 'tree')]
        result['domain'] = [('id', 'in', invoice_ids.ids)]
        #result['target'] = 'new'
        return result

    def clear_subscription_schedule(self):
        for record in self:
            record.subscription_schedule.invoice_ids = False


    def sync_invoice_to_term(self):
        for record in self:
            if not record.subscription_schedule:
                raise UserError('No existen plazos creados.')
            
            if record.invoice_ids:                    
                for inv in sorted(record.invoice_ids, key=lambda x: x.name):
                    if not inv.schedule_id:
                        for lsc in sorted(record.subscription_schedule, key=lambda x: x.date_due, reverse=True):
                            amount_recurring_taxinc =  lsc.amount_recurring_taxinc
                            total_invoiced = lsc.total_invoiced
                            if total_invoiced <= amount_recurring_taxinc:
                                invoiced_pending = amount_recurring_taxinc - total_invoiced
                                if inv.amount_total <= invoiced_pending:
                                    inv.schedule_id = lsc.id

                        if not inv.schedule_id:
                            record.write({
                                'invoice_warning_ids': [(4, inv.id)]
                            })
                

    def create_subscription_schedule(self):
        for order in self:
            msn = []
            if not order.recurrence_id:
                msn.append('La suscripción debe tener una "Recurrencia" establecida.')
            if not order.start_date:
                msn.append('La suscripción debe tener una "Fecha de inicio" establecida.')
            if not order.end_date:
                msn.append('La suscripción debe tener una "Fecha final" o "Hasta" establecida.')
            if order.amount_recurring_taxinc <= 0:
                msn.append('La suscripción debe tener un "Importe recurrente" mayor que CERO.')
            # añadir cuando hay facturas dentro de los plazos tampoco se pueda.            
            if msn:
                raise UserError("\n".join(msn))

            
            schedule_obj = self.env['sale.subscription.schedule']
            duration = order.recurrence_id.duration
            unit = order.recurrence_id.unit  # day, week, month, year
            period = relativedelta()  # Inicializamos el periodo
            start_date = order.start_date

            # Borrar cronogramas existentes para regenerar
            #schedule_obj.search([('order_id', '=', order.id)])
            for sc in order.subscription_schedule:
                sc.order_id = False
                sc.unlink()

            # Pre-calcular terms si existen para usarlos en el bucle
            terms = []
            if order.payment_term_id:
                # Calculo de terminos usando _compute_terms (Odoo 16)
                date_ref = start_date
                currency = order.currency_id
                company = order.company_id
                sign = 1
                
                untaxed_amount_currency = order.amount_untaxed
                tax_amount_currency = order.amount_tax
                
                if currency != company.currency_id:
                    untaxed_amount = currency._convert(untaxed_amount_currency, company.currency_id, company, date_ref)
                    tax_amount = currency._convert(tax_amount_currency, company.currency_id, company, date_ref)
                else:
                    untaxed_amount = untaxed_amount_currency
                    tax_amount = tax_amount_currency
                    
                terms = order.payment_term_id._compute_terms(
                    date_ref=date_ref,
                    currency=currency,
                    company=company,
                    tax_amount=tax_amount,
                    tax_amount_currency=tax_amount_currency,
                    sign=sign,
                    untaxed_amount=untaxed_amount,
                    untaxed_amount_currency=untaxed_amount_currency,
                    cash_rounding=None
                )

            remaining_amount = order.amount_total
            
            term_number = 0
            term_label = False
            total_period_recurrin = order.term_number
            
            if total_period_recurrin <= 0:
                total_period_recurrin = 1

            for i in range(0, total_period_recurrin):
                # Calcular la fecha de cada periodo
                if unit == 'month':
                    period = relativedelta(months=duration * i)
                elif unit == 'day':
                    period = relativedelta(days=duration * i)
                elif unit == 'week':
                    period = relativedelta(weeks=duration * i)
                elif unit == 'year':
                    period = relativedelta(years=duration * i)

                payment_date = start_date + period
                notification_date = payment_date # - relativedelta(days=order.recurrence_id.notification_days or 0)

                # Determinar el monto de la cuota
                amount_recurring_taxinc = 0.0
                
                if order.payment_term_id and terms:
                    if i < len(terms):
                         amount_recurring_taxinc = terms[i].get('foreign_amount', 0.0)
                    else:
                         # Si hay mas periodos que terminos, poner 0 o el resto en el ultimo
                         if i == total_period_recurrin - 1:
                             amount_recurring_taxinc = remaining_amount
                         else:
                             amount_recurring_taxinc = 0.0
                else:
                    # Fallback si no hay terms: dividir equitativamente
                    if total_period_recurrin > 0:
                        if i == total_period_recurrin - 1:
                            amount_recurring_taxinc = remaining_amount
                        else:
                            amount_recurring_taxinc = round(order.amount_total / total_period_recurrin, 2)
                    else:
                        amount_recurring_taxinc = order.amount_total
                
                remaining_amount -= amount_recurring_taxinc

                # Crear el cronograma de pago
                term_number += 1
                term_label = '%s de %s' % ( str(term_number).zfill(2) ,  str(total_period_recurrin).zfill(2) )
                schedule_obj.create({
                    'order_id': order.id,
                    'term_number': term_number,
                    'term_label': term_label,
                    'notification_date': notification_date,
                    'date_due': payment_date,
                    'date_schedule': payment_date,
                    'amount_recurring_taxinc': amount_recurring_taxinc,
                    'currency_id': order.currency_id.id,
                })

            _logger.info("Cronograma de pagos creado para la orden: %s", order.name)

    recurring_rule_count = fields.Integer(string="Número de pagos") # OLD: Se mantiene temporalmente


    sale_note_inv = fields.One2many('sale.note.inv', 'order_id', string='Registros Anteriores')
    amount_no_recurring_taxinc = fields.Monetary(compute='_compute_amount_recurring_taxinc', string="Importe no recurrente", store=True)    
    amount_recurring_taxinc = fields.Monetary(compute='_compute_amount_recurring_taxinc', string="Importe recurrente", store=True)
    

    invoice_warning_count = fields.Integer("Facturas a revisar")
    invoice_warning_ids = fields.Many2many(
        comodel_name='account.move',
        relation='order_war_account_war_rel',
        string="Invoice Warnings",
    )
        
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

    
    # No colocar el decorador model porque eso si llama a todos los records.
    def only_recurring_create_invoice(self):
        for record in self:
            record._create_recurring_invoice(automatic=True)

    # Renovar token
    def open_payment_method_url(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url').rstrip('/')
        payment_url = f"{base_url}/my/isep_payment_method_customer/{self.id}"

        return {
            'type': 'ir.actions.act_url',
            'url': payment_url,
            'target': 'new',
        }

    
    
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        if self.recurrence_id and not self.subscription_schedule:
            self.create_subscription_schedule()
        return res

    def _create_payment_transaction(self, vals):
        # Use sudo() to ensure we can read the schedule even if the user is public/portal
        order_sudo = self.sudo()
        if order_sudo.subscription_schedule:
            # Prioritize the first unpaid schedule line amount
            first_unpaid = order_sudo.subscription_schedule.filtered(lambda s: s.payment_state == 'not_paid').sorted('date_due')
            if first_unpaid:
                installment_amount = first_unpaid[0].amount_recurring_taxinc
                
                # If the passed amount is the total, we assume we want to charge the installment
                # Use order_sudo.amount_total to avoid Access Errors
                current_total = order_sudo.amount_total
                if vals.get('amount') and abs(vals['amount'] - current_total) < 0.01:
                     vals['amount'] = installment_amount
            
        return super(SaleOrder, self)._create_payment_transaction(vals)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Attempt to find the related sale order
            order = False
            # Check sale_order_ids (Many2many)
            if vals.get('sale_order_ids'):
                commands = vals['sale_order_ids']
                # Handle [(6, 0, [ids])]
                for cmd in commands:
                    if cmd[0] == 6 and cmd[2]:
                        order_id = cmd[2][0]
                        order = self.env['sale.order'].sudo().browse(order_id)
                        break
            
            # Fallback: Check reference
            if not order and vals.get('reference'):
                order = self.env['sale.order'].sudo().search([('name', '=', vals['reference'])], limit=1)
            
            if order:
                # Check for subscription schedule
                if hasattr(order, 'subscription_schedule') and order.subscription_schedule:
                     first_unpaid = order.subscription_schedule.filtered(lambda s: s.payment_state == 'not_paid').sorted('date_due')
                     if first_unpaid:
                         installment_amount = first_unpaid[0].amount_recurring_taxinc
                         current_amount = vals.get('amount', 0.0)
                         
                         # If amount matches total, override it
                         if abs(current_amount - order.amount_total) < 0.01:
                             vals['amount'] = installment_amount
        
        return super(PaymentTransaction, self).create(vals_list)

    def _reconcile_after_done(self):
        # Override to handle subscription partial payments (installments)
        for tx in self:
            if tx.sale_order_ids:
                for order in tx.sale_order_ids:
                    if hasattr(order, 'subscription_schedule') and order.subscription_schedule and order.state in ('draft', 'sent'):
                        # Check if amount matches any unpaid installment
                        # We prioritize the first unpaid one
                        first_unpaid = order.subscription_schedule.filtered(lambda s: s.payment_state == 'not_paid').sorted('date_due')
                        if first_unpaid:
                            installment_amount = first_unpaid[0].amount_recurring_taxinc
                            # Allow a small difference for rounding
                            if abs(tx.amount - installment_amount) < 0.01:
                                order.sudo().action_confirm()
                                # Force invoice creation for the full amount (Factura Global)
                                invoices = order.sudo()._create_invoices()
                                if invoices:
                                    invoices.sudo().action_post()
                                # We manually confirm it, so super() won't complain about mismatch because state is now 'sale'
        
        return super(PaymentTransaction, self)._reconcile_after_done()
