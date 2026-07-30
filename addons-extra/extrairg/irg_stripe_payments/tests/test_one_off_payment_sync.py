# -*- coding: utf-8 -*-
from unittest.mock import patch

from odoo.tests.common import tagged

from .common import StripePaymentsCommon


@tagged('post_install', '-at_install')
class TestOneOffPaymentSync(StripePaymentsCommon):

    def test_01_payment_intent_without_invoice_creates_row(self):
        """El agujero principal: antes esto no dejaba ningún rastro en Odoo."""
        partner = self._make_partner('Ana', 'ana@test.com', irg_stripe_customer_id='cus_A')

        self.sync._sync_payment_intent_succeeded(
            self._payment_intent('pi_one_off_1', customer='cus_A'))

        payment = self.payment_obj.search([('stripe_id', '=', 'pi_one_off_1')])
        self.assertEqual(len(payment), 1)
        self.assertEqual(payment.partner_id, partner)
        self.assertEqual(payment.partner_state, 'linked')
        self.assertEqual(payment.partner_match_method, 'stripe_customer_id')
        self.assertEqual(payment.state, 'succeeded')
        self.assertEqual(payment.amount, 50.0)
        self.assertFalse(payment.is_subscription_payment)
        self.assertEqual(payment.stripe_charge_id, 'ch_test_1')

    def test_02_same_payment_intent_twice_is_one_row(self):
        self._make_partner('Bea', 'bea@test.com', irg_stripe_customer_id='cus_B')
        payload = self._payment_intent('pi_dup_1', customer='cus_B')

        self.sync._sync_payment_intent_succeeded(payload)
        self.sync._sync_payment_intent_succeeded(payload)

        payments = self.payment_obj.search([('stripe_id', '=', 'pi_dup_1')])
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments.amount, 50.0)

    def test_03_unresolvable_payment_goes_to_review(self):
        self.sync._sync_payment_intent_succeeded(
            self._payment_intent('pi_orphan_1', customer=None, email='nadie@test.com'))

        payment = self.payment_obj.search([('stripe_id', '=', 'pi_orphan_1')])
        self.assertEqual(payment.partner_state, 'review')
        self.assertFalse(payment.partner_id)
        self.assertTrue(payment.review_id)
        self.assertEqual(payment.review_id.reason, 'not_found')

    def test_04_payment_transaction_wins_over_email(self):
        """La transacción de Odoo es la señal más fiable y hoy nadie la usaba."""
        tx_partner = self._make_partner('Carla Correcta', 'carla@test.com')
        # Un homónimo con el mismo email: si ganara el email, el pago acabaría aquí.
        self._make_partner('Carla Impostora', 'carla@test.com')

        tx = self.env['payment.transaction'].sudo().create({
            'provider_id': self.provider.id,
            'reference': 'TEST-TX-001',
            'provider_reference': 'pi_with_tx_1',
            'amount': 50.0,
            'currency_id': self.env.company.currency_id.id,
            'partner_id': tx_partner.id,
        })

        self.sync._sync_payment_intent_succeeded(
            self._payment_intent('pi_with_tx_1', email='carla@test.com'))

        payment = self.payment_obj.search([('stripe_id', '=', 'pi_with_tx_1')])
        self.assertEqual(payment.partner_id, tx_partner)
        self.assertEqual(payment.partner_match_method, 'payment_transaction')
        self.assertEqual(payment.payment_transaction_id, tx)

    def test_05_client_reference_id_identifies_partner(self):
        partner = self._make_partner('Dani', 'dani@test.com')
        session = {
            'id': 'cs_test_1',
            'object': 'checkout.session',
            'mode': 'payment',
            'payment_intent': 'pi_from_session_1',
            'client_reference_id': 'odoo_partner_%s' % partner.id,
            'amount_total': 12500,
            'currency': 'eur',
            'created': 1700000000,
            'metadata': {},
        }
        # Stripe no devuelve el PaymentIntent: se construye con lo que trae la sesión.
        with patch.object(type(self.provider), '_stripe_make_request', return_value={}):
            self.sync._sync_checkout_session(session)

        payment = self.payment_obj.search([('stripe_id', '=', 'pi_from_session_1')])
        self.assertEqual(len(payment), 1)
        self.assertEqual(payment.partner_id, partner)
        self.assertEqual(payment.partner_match_method, 'client_reference_id')
        self.assertEqual(payment.stripe_checkout_session_id, 'cs_test_1')
        self.assertEqual(payment.amount, 125.0)

    def test_06_session_then_payment_intent_merge_into_one_row(self):
        partner = self._make_partner('Elena', 'elena@test.com')
        session = {
            'id': 'cs_merge_1',
            'object': 'checkout.session',
            'mode': 'payment',
            'payment_intent': 'pi_merge_1',
            'client_reference_id': 'odoo_partner_%s' % partner.id,
            'amount_total': 5000,
            'currency': 'eur',
            'created': 1700000000,
            'metadata': {},
        }
        with patch.object(type(self.provider), '_stripe_make_request', return_value={}):
            self.sync._sync_checkout_session(session)

        # El PaymentIntent llega después y no trae ninguna pista de identidad.
        self.sync._sync_payment_intent_succeeded(self._payment_intent('pi_merge_1'))

        payments = self.payment_obj.search([('stripe_id', '=', 'pi_merge_1')])
        self.assertEqual(len(payments), 1)
        # El match de mayor confianza no se degrada.
        self.assertEqual(payments.partner_id, partner)
        self.assertEqual(payments.partner_match_method, 'client_reference_id')
        # Y la sesión no se pierde.
        self.assertEqual(payments.stripe_checkout_session_id, 'cs_merge_1')

    def test_07_subscription_payment_still_reconciles_once(self):
        """El ledger observa; la conciliación sigue siendo del módulo base."""
        self._make_partner('Fabio', 'fabio@test.com', irg_stripe_customer_id='cus_F')
        invoice_payload = {'id': 'in_sub_1', 'subscription': 'sub_1',
                           'status': 'paid', 'amount_paid': 5000}

        with patch.object(type(self.provider), '_stripe_make_request',
                          return_value=invoice_payload), \
                patch.object(type(self.sync), '_sync_invoice_paid') as mock_reconcile:
            self.sync._sync_payment_intent_succeeded(
                self._payment_intent('pi_sub_1', customer='cus_F', invoice='in_sub_1'))

        payment = self.payment_obj.search([('stripe_id', '=', 'pi_sub_1')])
        self.assertTrue(payment.is_subscription_payment)
        self.assertEqual(payment.stripe_invoice_id, 'in_sub_1')
        # La conciliación se delega exactamente una vez, como antes del cambio.
        self.assertEqual(mock_reconcile.call_count, 1)

    def test_08_charge_refunded_updates_existing_row(self):
        self._make_partner('Gina', 'gina@test.com', irg_stripe_customer_id='cus_G')
        self.sync._sync_payment_intent_succeeded(
            self._payment_intent('pi_refund_1', customer='cus_G', charge_id='ch_refund_1'))

        self.sync._irg_sync_charge_refunded(self._charge(
            'ch_refund_1', payment_intent='pi_refund_1', customer='cus_G',
            amount=5000, amount_refunded=5000, refunded=True))

        payments = self.payment_obj.search([('stripe_id', '=', 'pi_refund_1')])
        self.assertEqual(len(payments), 1, "El reembolso no debe crear una segunda fila")
        self.assertEqual(payments.state, 'refunded')
        self.assertEqual(payments.amount_refunded, 50.0)

    def test_09_partial_refund(self):
        self._make_partner('Hilda', 'hilda@test.com', irg_stripe_customer_id='cus_H')
        self.sync._sync_payment_intent_succeeded(
            self._payment_intent('pi_partial_1', customer='cus_H', charge_id='ch_partial_1'))

        self.sync._irg_sync_charge_refunded(self._charge(
            'ch_partial_1', payment_intent='pi_partial_1', customer='cus_H',
            amount=5000, amount_refunded=2000, refunded=False))

        payment = self.payment_obj.search([('stripe_id', '=', 'pi_partial_1')])
        self.assertEqual(payment.state, 'partially_refunded')
        self.assertEqual(payment.amount_refunded, 20.0)

    def test_10_failed_payment_intent_is_recorded(self):
        self._make_partner('Iker', 'iker@test.com', irg_stripe_customer_id='cus_I')

        self.sync.dispatch_event({
            'type': 'payment_intent.payment_failed',
            'data': {'object': self._payment_intent('pi_failed_1', customer='cus_I')},
        })

        payment = self.payment_obj.search([('stripe_id', '=', 'pi_failed_1')])
        self.assertEqual(payment.state, 'failed')

    def test_11_zero_decimal_currency(self):
        """JPY no tiene decimales: dividir por 100 a mano daría un importe 100x menor."""
        jpy = self.env['res.currency'].sudo().with_context(active_test=False).search(
            [('name', '=', 'JPY')], limit=1)
        if not jpy:
            self.skipTest("La divisa JPY no está disponible en esta base de datos")
        self._make_partner('Jun', 'jun@test.com', irg_stripe_customer_id='cus_J')

        self.sync._sync_payment_intent_succeeded(
            self._payment_intent('pi_jpy_1', amount=5000, currency='jpy', customer='cus_J'))

        payment = self.payment_obj.search([('stripe_id', '=', 'pi_jpy_1')])
        self.assertEqual(payment.amount, 5000.0)
        self.assertEqual(payment.currency_id, jpy)

    def test_12_unknown_currency_keeps_raw_code(self):
        self._make_partner('Kim', 'kim@test.com', irg_stripe_customer_id='cus_K')

        self.sync._sync_payment_intent_succeeded(
            self._payment_intent('pi_xxx_1', currency='zzz', customer='cus_K'))

        payment = self.payment_obj.search([('stripe_id', '=', 'pi_xxx_1')])
        self.assertFalse(payment.currency_id)
        self.assertEqual(payment.stripe_currency, 'ZZZ')

    def test_13_latest_charge_shape_is_supported(self):
        """Según la versión de API, el charge llega como `latest_charge` y no en `charges`."""
        self._make_partner('Lola', 'lola@test.com', irg_stripe_customer_id='cus_L')
        payload = {
            'id': 'pi_shape_1',
            'object': 'payment_intent',
            'amount': 5000,
            'currency': 'eur',
            'customer': 'cus_L',
            'created': 1700000000,
            'metadata': {},
            'latest_charge': {
                'id': 'ch_shape_1',
                'receipt_url': 'https://pay.stripe.com/receipts/shape',
                'billing_details': {'email': 'lola@test.com'},
            },
        }

        self.sync._sync_payment_intent_succeeded(payload)

        payment = self.payment_obj.search([('stripe_id', '=', 'pi_shape_1')])
        self.assertEqual(payment.stripe_charge_id, 'ch_shape_1')
        self.assertEqual(payment.receipt_url, 'https://pay.stripe.com/receipts/shape')

    def test_14_partner_totals_and_student_button(self):
        partner = self._make_partner('Marta', 'marta@test.com', irg_stripe_customer_id='cus_M')
        student = self._make_student(partner)

        self.sync._sync_payment_intent_succeeded(
            self._payment_intent('pi_total_1', amount=5000, customer='cus_M'))
        self.sync._sync_payment_intent_succeeded(
            self._payment_intent('pi_total_2', amount=2500, customer='cus_M',
                                 charge_id='ch_total_2'))

        partner.invalidate_recordset()
        self.assertEqual(partner.irg_stripe_payment_count, 2)
        student.invalidate_recordset()
        self.assertEqual(student.irg_stripe_payment_count, 2)
