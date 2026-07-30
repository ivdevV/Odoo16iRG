# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError
from odoo.tests.common import tagged

from .common import StripePaymentsCommon


@tagged('post_install', '-at_install')
class TestSecurity(StripePaymentsCommon):

    def setUp(self):
        super().setUp()
        self.plain_user = self.env['res.users'].sudo().create({
            'name': 'Usuario interno raso',
            'login': 'irg_stripe_plain_user',
            'email': 'plain@test.com',
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

    def test_01_plain_user_cannot_create_payments(self):
        """Las filas las genera la máquina: nadie salvo administración crea o borra."""
        with self.assertRaises(AccessError):
            self.env['irg.stripe.payment'].with_user(self.plain_user).create({
                'stripe_id': 'pi_forged_1',
                'amount': 100.0,
            })

    def test_02_plain_user_cannot_delete_payments(self):
        payment = self.payment_obj.create({'stripe_id': 'pi_todelete_1', 'amount': 10.0})
        with self.assertRaises(AccessError):
            payment.with_user(self.plain_user).unlink()

    def test_03_resolving_a_review_is_checked_server_side(self):
        """Ocultar el botón no es seguridad: el chequeo va en el método."""
        review = self.review_obj.create({
            'reason': 'ambiguous_email',
            'stripe_email': 'dup@test.com',
            'stripe_object_id': 'pi_sec_1',
        })
        with self.assertRaises(AccessError):
            review.with_user(self.plain_user)._check_can_resolve()

    def test_04_plain_user_cannot_run_backfill(self):
        with self.assertRaises(AccessError):
            self.env['irg.stripe.backfill.wizard'].with_user(self.plain_user).create({
                'provider_id': self.provider.id,
                'date_from': '2026-01-01',
                'date_to': '2026-01-07',
            })
