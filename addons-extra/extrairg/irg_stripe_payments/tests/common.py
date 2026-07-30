# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class StripePaymentsCommon(TransactionCase):
    """Base compartida. Stripe siempre mockeado: los tests no salen a la red."""

    def setUp(self):
        super().setUp()
        self.sync = self.env['stripe.sync'].sudo()
        self.payment_obj = self.env['irg.stripe.payment'].sudo()
        self.review_obj = self.env['irg.stripe.identity.review'].sudo()
        self.provider = self._ensure_stripe_provider()
        self._set_email_mode('strict_unique')

    def _ensure_stripe_provider(self):
        vals = {
            'name': 'Stripe',
            'code': 'stripe',
            'state': 'test',
            'stripe_publishable_key': 'pk_test_mock',
            'stripe_secret_key': 'sk_test_mock',
        }
        provider = self.env['payment.provider'].sudo().search([('code', '=', 'stripe')], limit=1)
        if provider:
            provider.write(vals)
        else:
            provider = self.env['payment.provider'].sudo().create(vals)
        return provider

    def _set_email_mode(self, mode):
        self.env['ir.config_parameter'].sudo().set_param(
            'irg_stripe.email_match_mode', mode)

    def _make_partner(self, name, email=None, **kwargs):
        vals = {'name': name}
        if email:
            vals['email'] = email
        vals.update(kwargs)
        return self.env['res.partner'].sudo().create(vals)

    def _make_student(self, partner):
        return self.env['op.student'].sudo().create({
            'partner_id': partner.id,
            'first_name': partner.name,
            'last_name': 'Test',
            'birth_date': '2000-01-01',
            'gender': 'm',
        })

    # ------------------------------------------------------------------
    # Payloads
    # ------------------------------------------------------------------
    def _payment_intent(self, stripe_id='pi_test_1', amount=5000, currency='eur',
                        customer=None, invoice=None, email=None, metadata=None,
                        created=1700000000, charge_id='ch_test_1'):
        charge = {
            'id': charge_id,
            'object': 'charge',
            'receipt_url': 'https://pay.stripe.com/receipts/test',
            'billing_details': {'email': email} if email else {},
        }
        return {
            'id': stripe_id,
            'object': 'payment_intent',
            'amount': amount,
            'amount_received': amount,
            'currency': currency,
            'customer': customer,
            'invoice': invoice,
            'created': created,
            'status': 'succeeded',
            'description': 'Test payment',
            'metadata': metadata or {},
            'charges': {'data': [charge]},
        }

    def _charge(self, stripe_id='ch_test_1', payment_intent=None, amount=5000,
                currency='eur', customer=None, email=None, amount_refunded=0,
                refunded=False, created=1700000000, invoice=None):
        return {
            'id': stripe_id,
            'object': 'charge',
            'payment_intent': payment_intent,
            'amount': amount,
            'amount_refunded': amount_refunded,
            'refunded': refunded,
            'currency': currency,
            'customer': customer,
            'invoice': invoice,
            'created': created,
            'status': 'succeeded',
            'receipt_url': 'https://pay.stripe.com/receipts/test',
            'billing_details': {'email': email} if email else {},
            'metadata': {},
        }
