# -*- coding: utf-8 -*-
"""Un contacto con varios Customers de Stripe.

Todos estos casos venían del comportamiento observado en beta: un contacto con cinco
Customers legítimos del que solo se reconocía uno, revisiones que al resolverse no
cambiaban nada, y una fila de revisión por cada pago del mismo problema.
"""
from contextlib import contextmanager
from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import StripePaymentsCommon


@tagged('post_install', '-at_install')
class TestMultiCustomerIdentity(StripePaymentsCommon):

    def setUp(self):
        super().setUp()
        self.customer_obj = self.env['irg.stripe.customer'].sudo()
        self.partner = self._make_partner('Multi Customer', 'multi@test.com')

    @contextmanager
    def _no_stripe_api(self):
        """Corta la salida a la API.

        Sin esto, resolver un Customer desconocido intenta un `GET customers/{id}`
        real: con la clave falsa devuelve 401, el `except` lo traga y el test pasa
        igual, pero cada ejecución sale a internet. Un test no debe depender de la red.
        """
        with patch.object(type(self.provider), '_stripe_make_request', return_value={}):
            yield

    # ------------------------------------------------------------------
    # El modelo admite varios
    # ------------------------------------------------------------------
    def test_01_partner_accepts_several_customers(self):
        self.customer_obj._irg_register(self.partner, 'cus_A')
        self.customer_obj._irg_register(self.partner, 'cus_B')
        self.customer_obj._irg_register(self.partner, 'cus_C')
        self.assertEqual(self.partner.irg_stripe_customer_count, 3)

    def test_02_first_customer_syncs_legacy_field(self):
        """El Char antiguo lo siguen leyendo otros módulos: no puede quedarse vacío."""
        self.customer_obj._irg_register(self.partner, 'cus_A')
        self.partner.invalidate_recordset()
        self.assertEqual(self.partner.irg_stripe_customer_id, 'cus_A')

    def test_03_second_customer_does_not_overwrite_legacy(self):
        self.customer_obj._irg_register(self.partner, 'cus_A')
        self.customer_obj._irg_register(self.partner, 'cus_B')
        self.partner.invalidate_recordset()
        self.assertEqual(self.partner.irg_stripe_customer_id, 'cus_A')

    def test_04_registering_is_idempotent(self):
        self.customer_obj._irg_register(self.partner, 'cus_A')
        self.customer_obj._irg_register(self.partner, 'cus_A')
        self.assertEqual(self.partner.irg_stripe_customer_count, 1)

    def test_05_customer_of_another_partner_is_a_real_conflict(self):
        """Un Customer sí es de una sola persona. Eso sigue siendo conflicto."""
        other = self._make_partner('Otro', 'otro@test.com')
        self.customer_obj._irg_register(self.partner, 'cus_A')
        record, conflict = self.customer_obj._irg_register(other, 'cus_A')
        self.assertEqual(conflict, self.partner)

    # ------------------------------------------------------------------
    # Resolución automática
    # ------------------------------------------------------------------
    def test_06_any_registered_customer_resolves(self):
        """El fallo original: solo se reconocía el Customer del campo Char."""
        self.customer_obj._irg_register(self.partner, 'cus_A')
        self.customer_obj._irg_register(self.partner, 'cus_B')
        result = self.sync._resolve_partner('cus_B')
        self.assertEqual(result['partner'], self.partner)
        self.assertEqual(result['method'], 'stripe_customer_id')

    def test_07_second_customer_no_longer_raises_conflict(self):
        """Antes, el segundo Customer de una persona iba a la cola como conflicto."""
        self.sync._irg_link_customer_id(self.partner, 'cus_A')
        self.sync._irg_link_customer_id(self.partner, 'cus_B')
        reviews = self.review_obj.search([
            ('reason', '=', 'conflicting_customer_id'), ('state', '=', 'open')])
        self.assertFalse(reviews, "Varios Customers por persona es normal, no un conflicto")
        self.assertEqual(self.partner.irg_stripe_customer_count, 2)

    # ------------------------------------------------------------------
    # Agrupación de revisiones
    # ------------------------------------------------------------------
    def test_08_same_customer_groups_into_one_review(self):
        """Tres pagos ambiguos del mismo Customer eran tres revisiones idénticas."""
        self._make_partner('Dup Uno', 'dup@test.com')
        self._make_partner('Dup Dos', 'dup@test.com')
        with self._no_stripe_api():
            for i in (1, 2, 3):
                self.sync._sync_payment_intent_succeeded(self._payment_intent(
                    stripe_id='pi_group_%s' % i, customer='cus_group',
                    email='dup@test.com', charge_id='ch_group_%s' % i))
        reviews = self.review_obj.search([
            ('stripe_customer_id', '=', 'cus_group'), ('state', '=', 'open')])
        self.assertEqual(len(reviews), 1, "Debe agrupar por Customer, no por pago")
        self.assertEqual(reviews.occurrence_count, 3)

    # ------------------------------------------------------------------
    # Resolver arrastra
    # ------------------------------------------------------------------
    def test_09_resolving_links_all_payments_of_the_customer(self):
        """El fallo que motivó todo: solo se vinculaba el pago de esa revisión."""
        self._make_partner('Dup Uno', 'dup2@test.com')
        self._make_partner('Dup Dos', 'dup2@test.com')
        with self._no_stripe_api():
            for i in (1, 2, 3):
                self.sync._sync_payment_intent_succeeded(self._payment_intent(
                    stripe_id='pi_all_%s' % i, customer='cus_all',
                    email='dup2@test.com', charge_id='ch_all_%s' % i))

        review = self.review_obj.search([
            ('stripe_customer_id', '=', 'cus_all'), ('state', '=', 'open')], limit=1)
        summary = review._irg_apply_partner(self.partner)

        self.assertEqual(summary['payments'], 3)
        payments = self.payment_obj.search([('stripe_customer_id', '=', 'cus_all')])
        self.assertTrue(all(p.partner_id == self.partner for p in payments))
        self.assertTrue(all(p.partner_state == 'linked' for p in payments))

    def test_10_resolving_registers_the_customer(self):
        self._make_partner('Dup Uno', 'dup3@test.com')
        self._make_partner('Dup Dos', 'dup3@test.com')
        with self._no_stripe_api():
            self.sync._sync_payment_intent_succeeded(self._payment_intent(
                stripe_id='pi_reg_1', customer='cus_reg', email='dup3@test.com',
                charge_id='ch_reg_1'))
        review = self.review_obj.search([
            ('stripe_customer_id', '=', 'cus_reg'), ('state', '=', 'open')], limit=1)
        review._irg_apply_partner(self.partner)
        self.assertIn('cus_reg', self.partner.irg_stripe_customer_ids.mapped('stripe_id'))

    def test_11_resolving_closes_sibling_reviews(self):
        """Dos motivos distintos sobre el mismo Customer se cierran juntos."""
        review_a = self.review_obj._log_issue(
            reason='not_found', stripe_customer_id='cus_sib')
        review_b = self.review_obj._log_issue(
            reason='conflicting_customer_id', stripe_customer_id='cus_sib')
        summary = review_a._irg_apply_partner(self.partner)
        self.assertEqual(summary['reviews'], 1)
        self.assertEqual(review_b.state, 'resolved')

    def test_12_payments_of_another_partner_are_not_stolen(self):
        """Mover dinero de una persona a otra en silencio es lo que hay que evitar."""
        other = self._make_partner('Dueño Real', 'dueno@test.com')
        payment = self.payment_obj.create({
            'stripe_id': 'pi_owned',
            'stripe_customer_id': 'cus_owned',
            'amount': 100.0,
            'partner_id': other.id,
            'partner_state': 'linked',
        })
        review = self.review_obj._log_issue(
            reason='not_found', stripe_customer_id='cus_owned')
        summary = review._irg_apply_partner(self.partner)
        self.assertEqual(summary['skipped'], 1)
        self.assertEqual(payment.partner_id, other, "No se le puede quitar el pago")

    def test_13_conflict_with_other_partner_blocks_resolution(self):
        other = self._make_partner('Ya Tiene', 'yatiene@test.com')
        self.customer_obj._irg_register(other, 'cus_taken')
        review = self.review_obj._log_issue(
            reason='not_found', stripe_customer_id='cus_taken')
        with self.assertRaises(UserError):
            review._irg_apply_partner(self.partner)

    def test_14_review_without_payments_is_flagged_in_preview(self):
        """La resolución fantasma: resolver algo que no cambia nada, sin avisar."""
        review = self.review_obj._log_issue(
            reason='conflicting_customer_id', stripe_customer_id='cus_empty')
        wizard = self.env['irg.stripe.identity.link.wizard'].sudo().create({
            'review_id': review.id,
            'partner_id': self.partner.id,
        })
        self.assertIn('no tiene pagos asociados', wizard.impact_preview)
