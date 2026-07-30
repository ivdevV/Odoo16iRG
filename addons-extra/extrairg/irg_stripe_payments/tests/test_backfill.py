# -*- coding: utf-8 -*-
from datetime import date, timedelta
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import tagged

from .common import StripePaymentsCommon


@tagged('post_install', '-at_install')
class TestBackfill(StripePaymentsCommon):

    def setUp(self):
        super().setUp()
        self.backfill = self.env['irg.stripe.backfill'].sudo()
        self.calls = []
        # Sin esto cada página costaría 0.2 s reales de test.
        sleep_patcher = patch('odoo.addons.irg_stripe_payments.models.irg_stripe_backfill.time.sleep')
        sleep_patcher.start()
        self.addCleanup(sleep_patcher.stop)

    def _paged_side_effect(self, pages):
        """Devuelve un side_effect que registra los endpoints pedidos."""
        def _side_effect(endpoint, **kwargs):
            self.calls.append(endpoint)
            if not pages:
                return {'data': [], 'has_more': False}
            return pages.pop(0)
        return _side_effect

    def test_01_pagination_uses_starting_after_in_endpoint(self):
        """El query string tiene que ir en el endpoint: `payload` viaja como body y
        Stripe lo ignora en un GET."""
        self._make_partner('Ana', 'ana@test.com', irg_stripe_customer_id='cus_A')
        pages = [
            {'data': [self._charge('ch_p1', payment_intent='pi_p1', customer='cus_A')],
             'has_more': True},
            {'data': [self._charge('ch_p2', payment_intent='pi_p2', customer='cus_A')],
             'has_more': False},
        ]
        with patch.object(type(self.provider), '_stripe_make_request',
                          side_effect=self._paged_side_effect(pages)):
            summary = self.backfill._run(self.provider, 1700000000, 1700086400, resume=False)

        self.assertEqual(len(self.calls), 2)
        self.assertNotIn('starting_after', self.calls[0])
        self.assertIn('starting_after=ch_p1', self.calls[1])
        self.assertIn('created[gte]=1700000000', self.calls[0])
        self.assertIn('created[lte]=1700086400', self.calls[0])
        self.assertEqual(summary['status'], 'done')
        self.assertEqual(summary['created'], 2)

    def test_02_rerun_is_idempotent(self):
        self._make_partner('Bea', 'bea@test.com', irg_stripe_customer_id='cus_B')
        charge = self._charge('ch_idem', payment_intent='pi_idem', customer='cus_B')

        for _run in range(2):
            with patch.object(type(self.provider), '_stripe_make_request',
                              side_effect=self._paged_side_effect(
                                  [{'data': [charge], 'has_more': False}])):
                self.backfill._run(self.provider, 1700000000, 1700086400, resume=False)

        payments = self.payment_obj.search([('stripe_id', '=', 'pi_idem')])
        self.assertEqual(len(payments), 1)
        self.assertEqual(payments.amount, 50.0)

    def test_03_two_charges_of_one_payment_intent_collapse(self):
        """Un reintento genera dos charges del mismo PaymentIntent: una sola fila."""
        self._make_partner('Carla', 'carla@test.com', irg_stripe_customer_id='cus_C')
        pages = [{'data': [
            self._charge('ch_retry_1', payment_intent='pi_retry', customer='cus_C'),
            self._charge('ch_retry_2', payment_intent='pi_retry', customer='cus_C'),
        ], 'has_more': False}]

        with patch.object(type(self.provider), '_stripe_make_request',
                          side_effect=self._paged_side_effect(pages)):
            self.backfill._run(self.provider, 1700000000, 1700086400, resume=False)

        self.assertEqual(len(self.payment_obj.search([('stripe_id', '=', 'pi_retry')])), 1)

    def test_04_charge_without_payment_intent_is_keyed_by_charge(self):
        """Los cobros legacy y de Terminal no tienen PaymentIntent: por eso se pagina
        `charges` y no `payment_intents`, donde serían invisibles."""
        self._make_partner('Dani', 'dani@test.com', irg_stripe_customer_id='cus_D')
        pages = [{'data': [self._charge('ch_legacy', payment_intent=None, customer='cus_D')],
                  'has_more': False}]

        with patch.object(type(self.provider), '_stripe_make_request',
                          side_effect=self._paged_side_effect(pages)):
            self.backfill._run(self.provider, 1700000000, 1700086400, resume=False)

        payment = self.payment_obj.search([('stripe_id', '=', 'ch_legacy')])
        self.assertEqual(len(payment), 1)
        self.assertEqual(payment.stripe_charge_id, 'ch_legacy')

    def test_05_api_failure_yields_partial_and_persists_cursor(self):
        """`_stripe_make_request` lanza ante un 4xx; no devuelve {'error': ...}."""
        self._make_partner('Elena', 'elena@test.com', irg_stripe_customer_id='cus_E')
        state = {'page': 0}

        def _side_effect(endpoint, **kwargs):
            self.calls.append(endpoint)
            state['page'] += 1
            if state['page'] == 1:
                return {'data': [self._charge('ch_ok', payment_intent='pi_ok',
                                              customer='cus_E')], 'has_more': True}
            raise ValidationError("429 Too Many Requests")

        with patch.object(type(self.provider), '_stripe_make_request', side_effect=_side_effect):
            summary = self.backfill._run(self.provider, 1700000000, 1700086400, resume=False)

        self.assertEqual(summary['status'], 'partial')
        self.assertEqual(summary['cursor'], 'ch_ok')
        cursor = self.env['ir.config_parameter'].sudo().get_param('irg_stripe.backfill_cursor')
        self.assertEqual(cursor, 'ch_ok')
        # La primera página sí se guardó: el trabajo hecho no se pierde.
        self.assertTrue(self.payment_obj.search([('stripe_id', '=', 'pi_ok')]))

    def test_06_resume_continues_from_saved_cursor(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'irg_stripe.backfill_cursor', 'ch_previous')

        with patch.object(type(self.provider), '_stripe_make_request',
                          side_effect=self._paged_side_effect(
                              [{'data': [], 'has_more': False}])):
            self.backfill._run(self.provider, 1700000000, 1700086400, resume=True)

        self.assertIn('starting_after=ch_previous', self.calls[0])

    def test_07_dry_run_writes_nothing(self):
        self._make_partner('Fran', 'fran@test.com', irg_stripe_customer_id='cus_F')
        pages = [{'data': [self._charge('ch_dry', payment_intent='pi_dry', customer='cus_F')],
                  'has_more': False}]

        with patch.object(type(self.provider), '_stripe_make_request',
                          side_effect=self._paged_side_effect(pages)):
            summary = self.backfill._run(
                self.provider, 1700000000, 1700086400, resume=False, dry_run=True)

        self.assertEqual(summary['scanned'], 1)
        self.assertEqual(summary['created'], 0)
        self.assertFalse(self.payment_obj.search([('stripe_id', '=', 'pi_dry')]))

    def test_08_window_longer_than_max_is_rejected(self):
        today = date.today()
        with self.assertRaises(UserError):
            self.backfill._check_window(today - timedelta(days=200), today)

    def test_09_inverted_window_is_rejected(self):
        today = date.today()
        with self.assertRaises(UserError):
            self.backfill._check_window(today, today - timedelta(days=5))

    def test_10_refunded_charge_state_from_backfill(self):
        self._make_partner('Gema', 'gema@test.com', irg_stripe_customer_id='cus_G')
        pages = [{'data': [self._charge(
            'ch_ref', payment_intent='pi_ref', customer='cus_G',
            amount=5000, amount_refunded=5000, refunded=True)], 'has_more': False}]

        with patch.object(type(self.provider), '_stripe_make_request',
                          side_effect=self._paged_side_effect(pages)):
            self.backfill._run(self.provider, 1700000000, 1700086400, resume=False)

        payment = self.payment_obj.search([('stripe_id', '=', 'pi_ref')])
        self.assertEqual(payment.state, 'refunded')
        self.assertEqual(payment.amount_refunded, 50.0)

    def test_11_wizard_requires_stripe_provider_and_window(self):
        wizard = self.env['irg.stripe.backfill.wizard'].sudo().create({
            'provider_id': self.provider.id,
            'date_from': date.today() - timedelta(days=400),
            'date_to': date.today(),
            'dry_run': True,
        })
        with self.assertRaises(UserError):
            wizard.action_run()
