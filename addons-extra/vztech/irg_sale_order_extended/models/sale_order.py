# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import datetime
import logging


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    student_id = fields.Many2one('res.partner', string='Student', store=True)
    account_bank_id = fields.Many2one(
        'res.partner.bank', string='Bank Account')
    valid_mandate_id = fields.Many2one(
        'account.banking.mandate', string='Valid Mandate')
    card_number = fields.Char(string='Card Number', size=16)
    expiration_month = fields.Char(string='Expiration Month', size=2)
    expiration_year = fields.Char(string='Expiration Year', size=2)
    display_card_number = fields.Char(
        string='Display Card Number', size=16, compute="_compute_display_card_number")
    display_expiration_month = fields.Char(
        string='Display Expiration Month', size=2, compute="_compute_display_expiration_month")
    display_expiration_year = fields.Char(
        string='Display Expiration Year', size=2, compute="_compute_display_expiration_year")
    is_card_payment = fields.Boolean(
        string="Is Card Payment", compute='_compute_is_card_payment')
    is_transfer_payment = fields.Boolean(
        string="Is Transfer Payment", compute='_compute_is_transfer_payment')
    is_official = fields.Boolean(
        string='Is Official', compute="_compute_is_official")
    initial_payment = fields.Monetary(
        string='Initial Payment', compute="_compute_initial_payment", digits=(16, 2), currency_field='currency_id')
    rest_postponed = fields.Monetary(
        string='Rest Postponed', compute='_compute_rest_postponed', digits=(16, 2), currency_field='currency_id')
    monthly_payments = fields.Integer(
        string='Monthly Payments', compute='_compute_monthly_payments')
    monthly_value = fields.Monetary(
        string='Monthly Value', compute='_compute_monthly_value', digits=(16, 2), currency_field='currency_id')
    payment_date = fields.Datetime(string='Payment Date')

    @api.onchange('partner_id')
    def _onchange_student_id(self):
        if self.partner_id:
            self.student_id = self.partner_id

    @api.depends('payment_mode_id')
    def _compute_is_card_payment(self):
        for order in self:
            if order.payment_mode_id.name in ['Datáfono', 'Stripe']:
                order.is_card_payment = True
            else:
                order.is_card_payment = False

    @api.depends('payment_mode_id')
    def _compute_is_transfer_payment(self):
        for order in self:
            if order.payment_mode_id.name in ['IRG Domiciliado', 'Transferencia IRG']:
                order.is_transfer_payment = True
            else:
                order.is_transfer_payment = False

    @api.constrains('card_number')
    def _check_card_number(self):
        for order in self:
            if order.card_number and (not order.card_number.isdigit() or len(order.card_number) != 16):
                raise ValidationError(
                    "El número de la tarjeta debe contener 16 dígitos numéricos.")

    @api.constrains('expiration_month')
    def _check_expiration_month(self):
        for order in self:
            if order.expiration_month and (not order.expiration_month.isdigit() or int(order.expiration_month) < 1 or int(order.expiration_month) > 12):
                raise ValidationError(
                    "El mes de vencimiento debe ser un número entre 1 y 12.")

    @api.constrains('expiration_year')
    def _check_expiration_year(self):
        current_year = int(datetime.datetime.now().strftime("%y"))
        for order in self:
            if order.expiration_year and (not order.expiration_year.isdigit() or len(order.expiration_year) != 2 or int(order.expiration_year) < current_year):
                raise ValidationError(
                    "El año de vencimiento debe ser un número de 2 dígitos y no debe ser inferior al año actual.")

    @api.depends('card_number')
    def _compute_display_card_number(self):
        for order in self:
            order.display_card_number = order.card_number

    @api.depends('expiration_month')
    def _compute_display_expiration_month(self):
        for order in self:
            order.display_expiration_month = order.expiration_month

    @api.depends('expiration_year')
    def _compute_display_expiration_year(self):
        for order in self:
            order.display_expiration_year = order.expiration_year

    @api.depends('order_line.product_id.formation_type')
    def _compute_is_official(self):
        for order in self:
            order.is_official = any(
                line.product_id.formation_type == 'officialdom' for line in order.order_line)

    @api.depends('order_line')
    def _compute_initial_payment(self):
        for order in self:
            registration_lines = order.order_line.filtered(
                lambda line: line.product_id.formation_type == 'registration')
            logging.info('registration_lines: %s', registration_lines)
            discount_registration_lines = order.order_line.filtered(
                lambda line: line.product_id.formation_type == 'discount_registration')
            logging.info('discount_registration_lines: %s',
                         discount_registration_lines)
            registration_total = sum(
                registration_lines.mapped('price_unit'))
            logging.info('registration_total: %s', registration_total)
            discount_registration_total = sum(
                discount_registration_lines.mapped('price_unit'))
            logging.info('discount_registration_total: %s',
                         discount_registration_total)
            order.initial_payment = registration_total + discount_registration_total
            logging.info('initial_payment: %s', order.initial_payment)

    @api.depends('amount_total', 'initial_payment')
    def _compute_rest_postponed(self):
        for order in self:
            order.rest_postponed = order.amount_total - order.initial_payment

    @api.depends('payment_term_id.line_ids')
    def _compute_monthly_payments(self):
        for order in self:
            if order.payment_term_id:
                for line in order.payment_term_id.line_ids:
                    if line.value == 'balance':
                        order.monthly_payments = line.months
                        break
                else:
                    order.monthly_payments = 0
            else:
                order.monthly_payments = 0

    @api.depends('rest_postponed', 'monthly_payments')
    def _compute_monthly_value(self):
        for order in self:
            if order.monthly_payments != 0:
                order.monthly_value = order.rest_postponed / order.monthly_payments
            else:
                order.monthly_value = 0
