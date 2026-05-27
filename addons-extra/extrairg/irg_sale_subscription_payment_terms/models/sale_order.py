# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('recurrence_id', 'subscription_management')
    def _compute_start_date(self):
        for so in self:
            existing_date = so.start_date or so._origin.start_date
            if existing_date:
                so.start_date = existing_date
            else:
                so.start_date = fields.Date.context_today(so)


    def _get_payment_term_last_date(self, start_date=None):
        self.ensure_one()
        ref_date = start_date or fields.Date.today()
        _logger.info("=== DEBUG: _get_payment_term_last_date called with start_date=%s, payment_term_id=%s ===", ref_date, self.payment_term_id)
        if not self.payment_term_id:
            _logger.info("=== DEBUG: missing payment_term_id ===")
            return False
            
        currency = self.currency_id
        company = self.company_id
        sign = 1
        
        untaxed_amount_currency = self.amount_untaxed
        tax_amount_currency = self.amount_tax
        
        if currency != company.currency_id:
            untaxed_amount = currency._convert(untaxed_amount_currency, company.currency_id, company, ref_date)
            tax_amount = currency._convert(tax_amount_currency, company.currency_id, company, ref_date)
        else:
            untaxed_amount = untaxed_amount_currency
            tax_amount = tax_amount_currency
            
        try:
            terms = self.payment_term_id._compute_terms(
                date_ref=ref_date,
                currency=currency,
                company=company,
                tax_amount=tax_amount,
                tax_amount_currency=tax_amount_currency,
                sign=sign,
                untaxed_amount=untaxed_amount,
                untaxed_amount_currency=untaxed_amount_currency,
                cash_rounding=None
            )
            _logger.info("=== DEBUG: _compute_terms returned terms: %s ===", terms)
            if terms:
                return terms[-1].get('date')
        except Exception as e:
            _logger.warning("Error computing payment term last date for SO %s: %s", self.name, e)
        return False

    @api.onchange('term_number', 'recurrence_id', 'start_date', 'payment_term_id')
    def onchange_end_date_suscrip(self):
        _logger.info("=== DEBUG: onchange_end_date_suscrip called ===")
        
        # Capture current start dates to preserve manual edits or defaults
        start_dates = {}
        for order in self:
            start_dates[order.id] = order.start_date
            
        # When payment terms change, auto-update recurrence, term schedule plan, and number of terms
        for order in self:
            if order.payment_term_id:
                # 1. Update recurrence to Monthly if not set (or override if payment term changed)
                monthly_recurrence = self.env.ref('sale_temporal.recurrence_monthly', raise_if_not_found=False)
                if monthly_recurrence:
                    order.recurrence_id = monthly_recurrence.id
                
                # 2. Get term_number from the number of payment term lines
                term_number = len(order.payment_term_id.line_ids) or 1
                
                # 3. Find matching product.term.schedule (Plan de Suscripción)
                term_schedule = self.env['product.term.schedule'].sudo().search([
                    ('term_number', '=', term_number),
                    ('custom', '=', False)
                ], limit=1)
                
                if term_schedule:
                    order.term_number_id = term_schedule.id
                    order.term_number = term_schedule.term_number
                else:
                    order.term_number = term_number

        super().onchange_end_date_suscrip()
        
        # Restore captured start dates
        for order in self:
            old_start = start_dates.get(order.id)
            if old_start:
                order.start_date = old_start
                
        for order in self:
            _logger.info("=== DEBUG: processing order %s, start_date=%s, payment_term_id=%s ===", order.name, order.start_date, order.payment_term_id)
            if order.payment_term_id:
                ref_date = order.start_date or fields.Date.context_today(order)
                last_date = order._get_payment_term_last_date(ref_date)
                if last_date:
                    order.end_date = last_date
                    _logger.info("=== DEBUG: end_date set to %s ===", last_date)
                else:
                    # Fallback to standard duration calculation
                    if order.recurrence_id:
                        duration = order.recurrence_id.duration * order.term_number
                        unit = order.recurrence_id.unit
                        period = relativedelta()
                        if unit == 'month':
                            period = relativedelta(months=duration)
                        elif unit == 'day':
                            period = relativedelta(days=duration)
                        elif unit == 'week':
                            period = relativedelta(weeks=duration)
                        elif unit == 'year':
                            period = relativedelta(years=duration)
                        order.end_date = ref_date + period - relativedelta(days=1)
                        _logger.info("=== DEBUG: end_date set to fallback %s ===", order.end_date)

    def create_subscription_schedule(self):
        # Update end_date based on payment terms before calling super to pass validations
        for order in self:
            if order.payment_term_id:
                ref_date = order.start_date or fields.Date.today()
                last_date = order._get_payment_term_last_date(ref_date)
                if last_date:
                    order.end_date = last_date

        # Call super first to let all standard/extension creation logic run.
        # This ensures the schedules are generated, amounts are set, and single-invoice modifications are made.
        res = super().create_subscription_schedule()

        for order in self:
            if not order.payment_term_id or not order.subscription_schedule:
                continue

            start_date = order.start_date or fields.Date.today()
            currency = order.currency_id
            company = order.company_id
            sign = 1
            
            untaxed_amount_currency = order.amount_untaxed
            tax_amount_currency = order.amount_tax
            
            if currency != company.currency_id:
                untaxed_amount = currency._convert(untaxed_amount_currency, company.currency_id, company, start_date)
                tax_amount = currency._convert(tax_amount_currency, company.currency_id, company, start_date)
            else:
                untaxed_amount = untaxed_amount_currency
                tax_amount = tax_amount_currency
                
            try:
                terms = order.payment_term_id._compute_terms(
                    date_ref=start_date,
                    currency=currency,
                    company=company,
                    tax_amount=tax_amount,
                    tax_amount_currency=tax_amount_currency,
                    sign=sign,
                    untaxed_amount=untaxed_amount,
                    untaxed_amount_currency=untaxed_amount_currency,
                    cash_rounding=None
                )
            except Exception as e:
                _logger.warning("Error computing payment terms in subscription schedule adjustment: %s", e)
                continue
                
            if not terms:
                continue

            # Sort schedules by term_number to align them 1:1 with computed terms
            schedules = order.subscription_schedule.sorted('term_number')
            for i, schedule in enumerate(schedules):
                # Skip if it is already linked to a specific global invoice line
                if schedule.move_line_id:
                    continue
                if i < len(terms):
                    term_date = terms[i].get('date')
                    if term_date:
                        schedule.write({
                            'date_due': term_date,
                            'date_schedule': term_date,
                            'notification_date': term_date,
                        })
        return res
