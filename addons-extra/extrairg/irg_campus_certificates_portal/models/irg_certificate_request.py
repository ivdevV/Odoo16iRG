# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class IrgCertificateRequest(models.Model):
    _inherit = 'irg.certificate.request'

    student_id = fields.Many2one(
        'op.student',
        string='Estudiante',
        compute='_compute_student_id',
        store=True,
        index=True,
    )
    diploma_registry_id = fields.Many2one(
        'irg.diploma.registry',
        string='Registro de Diploma',
        copy=False,
    )
    stripe_checkout_session_id = fields.Char(
        string='ID de Sesión Stripe',
        copy=False,
        index=True,
    )
    stripe_payment_intent_id = fields.Char(
        string='ID del Intento de Pago Stripe',
        copy=False,
    )
    stripe_invoice_id = fields.Char(
        string='ID de Factura Stripe',
        copy=False,
    )
    stripe_invoice_url = fields.Char(
        string='Enlace de Factura Stripe',
        copy=False,
    )
    stripe_invoice_pdf = fields.Char(
        string='PDF de Factura Stripe',
        copy=False,
    )
    stripe_receipt_url = fields.Char(
        string='Enlace del Recibo Stripe',
        copy=False,
    )
    stripe_payment_status = fields.Char(
        string='Estado del Pago Stripe',
        copy=False,
    )
    payment_success_date = fields.Datetime(
        string='Fecha de Pago Exitoso',
        copy=False,
    )
    payment_amount = fields.Float(
        string='Importe de Pago',
        digits=(6, 2),
        copy=False,
    )
    payment_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda de Pago',
        copy=False,
    )
    payment_concept = fields.Char(
        string='Concepto de Pago',
        copy=False,
    )

    @api.depends('gradebook_student_id', 'gradebook_student_id.student_id')
    def _compute_student_id(self):
        for rec in self:
            if rec.gradebook_student_id and rec.gradebook_student_id.student_id:
                rec.student_id = rec.gradebook_student_id.student_id
            else:
                # Fallback: buscar estudiante por partner_id
                student = self.env['op.student'].sudo().search([('partner_id', '=', rec.partner_id.id)], limit=1)
                rec.student_id = student.id if student else False

    def _create_stripe_checkout_session(self):
        """
        Crea una Stripe Checkout Session para el pago único del certificado.
        """
        self.ensure_one()
        provider = self.env['payment.provider'].sudo().search([
            ('code', '=', 'stripe'),
            ('state', 'in', ('enabled', 'test'))
        ], limit=1)
        if not provider:
            raise ValidationError(_("No se ha configurado el proveedor de pago Stripe."))

        partner = self.partner_id
        customer_id = partner.stripe_customer_id or partner.irg_stripe_customer_id
        if not customer_id and hasattr(partner, '_irg_ensure_stripe_customer'):
            customer_id = partner._irg_ensure_stripe_customer(provider=provider)

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        success_url = f"{base_url}/campus/certificates/payment/success/{self.id}"
        cancel_url = f"{base_url}/campus/certificates/payment/cancel/{self.id}"

        # Obtener el label del tipo de documento para la descripción
        document_label = dict(self._fields['document_type'].selection).get(self.document_type, self.document_type)

        payload = {
            'cancel_url': cancel_url,
            'success_url': success_url,
            'mode': 'payment',
            'client_reference_id': f'cert_req_{self.id}',
            'metadata[certificate_request_id]': str(self.id),
            'metadata[certificate_request_name]': self.name or '',
            'line_items[0][price_data][currency]': 'eur',
            'line_items[0][price_data][unit_amount]': int(round(self.price_total * 100)),
            'line_items[0][price_data][product_data][name]': f"Solicitud de Certificado ({document_label}): {self.name}",
            'line_items[0][quantity]': 1,
            'invoice_creation[enabled]': 'true',
        }

        if customer_id:
            payload['customer'] = customer_id
        elif partner.email:
            payload['customer_email'] = partner.email

        try:
            response = provider._stripe_make_request("checkout/sessions", payload=payload, method="POST")
            if response and not response.get('error'):
                session_id = response.get('id')
                url = response.get('url')
                self.write({
                    'stripe_checkout_session_id': session_id,
                })
                return url
            else:
                error_msg = response.get('error', {}).get('message', 'Error desconocido')
                raise ValidationError(_("Error al crear sesión en Stripe: %s") % error_msg)
        except Exception as e:
            _logger.exception("Error al comunicarse con Stripe para el certificado %s", self.name)
            raise ValidationError(_("No se pudo conectar con Stripe: %s") % str(e))

    def _process_stripe_checkout_payment(self, session_obj):
        """
        Registra el pago de Stripe en la solicitud de certificado, guarda evidencias y avanza de estado.
        """
        self.ensure_one()
        provider = self.env['stripe.sync']._get_stripe_provider()
        
        # Recuperar la factura de Stripe si existe
        invoice_id = session_obj.get('invoice')
        invoice_url = False
        invoice_pdf = False
        if invoice_id and provider:
            try:
                inv_res = provider._stripe_make_request(f"invoices/{invoice_id}", method='GET')
                if inv_res and not inv_res.get('error'):
                    invoice_url = inv_res.get('hosted_invoice_url')
                    invoice_pdf = inv_res.get('invoice_pdf')
            except Exception:
                _logger.warning("No se pudo obtener la factura %s de Stripe", invoice_id)

        # Recuperar el recibo de Stripe desde el PaymentIntent
        payment_intent_id = session_obj.get('payment_intent')
        receipt_url = False
        if payment_intent_id and provider:
            try:
                pi_res = provider._stripe_make_request(f"payment_intents/{payment_intent_id}", method='GET')
                if pi_res and not pi_res.get('error'):
                    charges = pi_res.get('charges', {}).get('data', [])
                    if charges:
                        receipt_url = charges[0].get('receipt_url')
            except Exception:
                _logger.warning("No se pudo obtener el PaymentIntent %s de Stripe", payment_intent_id)

        # Moneda del pago
        currency_code = (session_obj.get('currency') or 'eur').upper()
        currency = self.env['res.currency'].sudo().search([('name', '=', currency_code)], limit=1)

        self.write({
            'stripe_checkout_session_id': session_obj.get('id'),
            'stripe_payment_intent_id': payment_intent_id,
            'stripe_invoice_id': invoice_id,
            'stripe_invoice_url': invoice_url,
            'stripe_invoice_pdf': invoice_pdf,
            'stripe_receipt_url': receipt_url,
            'stripe_payment_status': session_obj.get('payment_status'),
            'payment_success_date': fields.Datetime.now(),
            'payment_amount': session_obj.get('amount_total', 0) / 100.0,
            'payment_currency_id': currency.id if currency else False,
            'payment_concept': f"Pago de Certificado {self.name}",
        })

        # Procesar la lógica original de facturación y transiciones
        self._process_payment()

        # Si es físico, el plan pide transicionar a 'in_process'
        if self.certificate_type not in ('digital', 'custom'):
            self.state = 'in_process'

    def _generate_and_attach_pdf(self):
        """
        Heredar la generación de PDF para asociar el diploma generado con irg.diploma.registry.
        """
        super(IrgCertificateRequest, self)._generate_and_attach_pdf()
        if self.document_type == 'diploma' and self.attachment_id:
            # Buscar el diploma creado para esta solicitud.
            student = self.student_id or self.gradebook_student_id.student_id
            if not student:
                student = self.env['op.student'].sudo().search([('partner_id', '=', self.partner_id.id)], limit=1)
            
            diploma = self.env['irg.diploma.registry'].sudo().search([
                ('student_id', '=', student.id if student else False),
                ('attachment_id', '=', False)
            ], order='id desc', limit=1)
            
            if diploma:
                diploma.write({'attachment_id': self.attachment_id.id})
                self.diploma_registry_id = diploma.id
