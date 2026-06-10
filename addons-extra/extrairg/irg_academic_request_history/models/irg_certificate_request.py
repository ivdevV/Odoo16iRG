# -*- coding: utf-8 -*-

from odoo import api, fields, models


class IrgCertificateRequest(models.Model):
    _inherit = 'irg.certificate.request'

    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        compute='_compute_student_id',
        store=True,
        index=True,
        readonly=True,
    )
    diploma_registry_id = fields.Many2one(
        'irg.diploma.registry',
        string='Registro de Diploma',
        copy=False,
        readonly=True,
        index=True,
    )
    payment_amount = fields.Monetary(
        string='Importe de Pago',
        currency_field='payment_currency_id',
        copy=False,
        readonly=True,
    )
    payment_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda de Pago',
        copy=False,
        readonly=True,
        default=lambda self: self.env.company.currency_id,
    )
    payment_concept = fields.Char(
        string='Concepto de Pago',
        copy=False,
        readonly=True,
    )
    payment_success_date = fields.Datetime(
        string='Fecha de Pago Confirmado',
        copy=False,
        readonly=True,
    )
    stripe_checkout_session_id = fields.Char(
        string='Stripe Checkout Session',
        copy=False,
        readonly=True,
        index=True,
    )
    stripe_payment_intent_id = fields.Char(
        string='Stripe PaymentIntent',
        copy=False,
        readonly=True,
        index=True,
    )
    stripe_invoice_id = fields.Char(
        string='Factura Stripe',
        copy=False,
        readonly=True,
        index=True,
    )
    stripe_invoice_url = fields.Char(
        string='URL Factura Stripe',
        copy=False,
        readonly=True,
    )
    stripe_invoice_pdf = fields.Char(
        string='PDF Factura Stripe',
        copy=False,
        readonly=True,
    )
    stripe_receipt_url = fields.Char(
        string='Recibo Stripe',
        copy=False,
        readonly=True,
    )
    stripe_payment_status = fields.Char(
        string='Estado Pago Stripe',
        copy=False,
        readonly=True,
    )

    @api.depends('gradebook_student_id.student_id', 'partner_id')
    def _compute_student_id(self):
        Student = self.env['op.student'].sudo()
        for request in self:
            student = request.gradebook_student_id.student_id
            if not student and request.partner_id:
                student = Student.search([('partner_id', '=', request.partner_id.id)], limit=1)
            request.student_id = student
