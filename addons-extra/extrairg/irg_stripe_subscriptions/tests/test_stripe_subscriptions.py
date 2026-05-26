# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged
import json


@tagged('post_install', '-at_install')
class TestStripeSubscriptions(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Stripe Test Partner',
            'email': 'partner@test.com',
            'irg_stripe_customer_id': 'cus_test_123'
        })
        recurrence = self.env['sale.temporal.recurrence'].search([('unit', '=', 'month'), ('duration', '=', 1)], limit=1)
        if not recurrence:
            recurrence = self.env['sale.temporal.recurrence'].create({
                'duration': 1,
                'unit': 'month',
                'name': 'Monthly'
            })
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'recurrence_id': recurrence.id,
        })

    def test_01_write_override_compatibility(self):
        """Prueba que escribir una cadena (ID de Stripe) en stripe_subscription_id
        busca/crea el registro local stripe.subscription y lo asocia como Many2one."""
        # Escribimos un string en el Many2one
        self.order.write({
            'stripe_subscription_id': 'sub_test_write_compatibility'
        })
        
        # Validamos que se convirtió en una relación Many2one con el modelo
        sub_record = self.order.stripe_subscription_id
        self.assertTrue(sub_record, "Debería haber una suscripción asociada")
        self.assertEqual(sub_record.stripe_id, 'sub_test_write_compatibility')
        self.assertEqual(sub_record.partner_id, self.partner, "Debería estar asociada al partner de la orden")

    def test_02_idempotency_log(self):
        """Prueba que el log de eventos de Stripe evita duplicados y mantiene la idempotencia."""
        event_id = 'evt_test_123'
        event_type = 'customer.subscription.updated'
        
        log_obj = self.env['stripe.event.log']
        # Crear un primer log
        log_1 = log_obj.create({
            'event_id': event_id,
            'event_type': event_type,
            'payload': '{}',
            'processed': True
        })
        self.assertTrue(log_1)

        # Si intentamos crear un duplicado con SQL unique constraint debería fallar, 
        # pero a nivel de controlador se busca primero. Probamos que el constraint funciona:
        with self.assertRaises(Exception):
            with self.cr.savepoint():
                log_obj.create({
                    'event_id': event_id,
                    'event_type': event_type,
                    'payload': '{}',
                    'processed': False
                })

    def test_03_sync_subscription_created(self):
        """Prueba que la sincronización del evento customer.subscription.created crea
        los registros locales y los asocia correctamente a la venta."""
        sub_payload = {
            'id': 'sub_sync_test_999',
            'customer': 'cus_test_123',
            'status': 'active',
            'current_period_start': 1716654873,
            'current_period_end': 1719333273,
            'cancel_at_period_end': False,
            'latest_invoice': 'in_invoice_test_123',
            'metadata': {
                'odoo_order_id': str(self.order.id)
            },
            'items': {
                'data': [{
                    'price': {
                        'id': 'price_test_abc',
                        'product': 'prod_test_xyz',
                        'unit_amount': 9900,
                        'currency': 'eur',
                        'recurring': {
                            'interval': 'month'
                        }
                    }
                }]
            }
        }
        
        # Despachamos el evento simulado
        self.env['stripe.sync'].dispatch_event({
            'type': 'customer.subscription.created',
            'id': 'evt_sub_created_test',
            'data': {
                'object': sub_payload
            }
        })

        # Buscamos la suscripción creada
        subscription = self.env['stripe.subscription'].search([('stripe_id', '=', 'sub_sync_test_999')], limit=1)
        self.assertTrue(subscription, "La suscripción debería haber sido creada localmente.")
        self.assertEqual(subscription.status, 'active')
        self.assertEqual(subscription.amount, 99.00)
        self.assertEqual(subscription.interval, 'month')
        self.assertEqual(subscription.partner_id, self.partner)

        # Verificamos la vinculación en sale.order
        self.order.refresh()
        self.assertEqual(self.order.stripe_subscription_id, subscription)
        self.assertEqual(self.order.stripe_subscription_ref, 'sub_sync_test_999')
        self.assertEqual(self.order.stripe_subscription_state, 'active')

    def test_04_sync_subscription_deleted(self):
        """Prueba que cuando llega un evento de cancelación de suscripción,
        la venta asociada se cancela/suspende en Odoo."""
        # Primero creamos la suscripción y la vinculamos
        subscription = self.env['stripe.subscription'].create({
            'name': 'Sub a borrar',
            'stripe_id': 'sub_to_delete_123',
            'partner_id': self.partner.id,
            'status': 'active'
        })
        self.order.write({
            'stripe_subscription_id': subscription.id,
            'stripe_subscription_ref': 'sub_to_delete_123',
            'stripe_subscription_state': 'active'
        })

        # Enviamos el evento de eliminación
        sub_payload = {
            'id': 'sub_to_delete_123',
            'customer': 'cus_test_123',
            'status': 'canceled'
        }
        self.env['stripe.sync'].dispatch_event({
            'type': 'customer.subscription.deleted',
            'id': 'evt_sub_deleted_test',
            'data': {
                'object': sub_payload
            }
        })

        # Validamos estados actualizados
        subscription.refresh()
        self.assertEqual(subscription.status, 'canceled')

        self.order.refresh()
        self.assertEqual(self.order.stripe_subscription_state, 'canceled')
        self.assertTrue(self.order.subscription_suspended, "La suscripción de Odoo debería estar suspendida.")

    def test_05_sync_invoice_paid(self):
        """Prueba que el evento invoice.paid marca el plazo del cronograma como pagado."""
        subscription = self.env['stripe.subscription'].create({
            'name': 'Sub a pagar',
            'stripe_id': 'sub_to_pay_99',
            'partner_id': self.partner.id,
            'status': 'active'
        })
        self.order.write({
            'stripe_subscription_id': subscription.id,
            'stripe_subscription_ref': 'sub_to_pay_99',
            'stripe_subscription_state': 'active'
        })

        # Creamos una línea de cronograma de prueba
        schedule = self.env['sale.subscription.schedule'].create({
            'order_id': self.order.id,
            'date_due': '2026-06-25',
            'date_schedule': '2026-06-25',
            'payment_state': 'not_paid',
            'amount_recurring_taxinc': 360.53
        })

        # Enviamos el evento de invoice.paid
        invoice_payload = {
            'id': 'in_paid_test_123',
            'subscription': 'sub_to_pay_99',
            'status': 'paid',
            'amount_paid': 36053
        }
        self.env['stripe.sync'].dispatch_event({
            'type': 'invoice.paid',
            'id': 'evt_inv_paid_test',
            'data': {
                'object': invoice_payload
            }
        })

        # Validamos que el plazo pasó a estar pagado
        schedule.refresh()
        self.assertEqual(schedule.payment_state, 'paid', "El plazo del cronograma debería haberse marcado como pagado.")

    def test_06_payment_link_generation_payload(self):
        """Test that the payment link generation constructs the correct description, metadata, and cancel_at payload."""
        import datetime
        from unittest.mock import patch
        import time

        # Setup values on the order
        self.order.write({
            'term_number': 3,
            'amount_total': 300.0,
            'end_date': datetime.date.today() + datetime.timedelta(days=90),
        })

        provider_vals = {
            'name': 'Stripe',
            'code': 'stripe',
            'state': 'test',
            'stripe_publishable_key': 'pk_test_mock',
            'stripe_secret_key': 'sk_test_mock',
        }
        provider = self.env['payment.provider'].sudo().search([
            ('code', '=', 'stripe'),
        ], limit=1)
        if not provider:
            # Create a mock provider if none exists for tests
            provider = self.env['payment.provider'].create(provider_vals)
        else:
            provider.write(provider_vals)

        # Mock _irg_ensure_stripe_price and _stripe_make_request
        with patch.object(type(self.order), '_irg_ensure_stripe_price', return_value='price_abc_123'), \
             patch.object(type(provider), '_stripe_make_request') as mock_req:

            mock_req.return_value = {
                'id': 'plink_test_123',
                'url': 'https://stripe.com/plink_test_123',
                'active': True,
                'metadata': {
                    'odoo_order_id': str(self.order.id),
                    'odoo_order_name': self.order.name
                }
            }

            self.order.action_irg_create_stripe_payment_link()

            # Check mock call payload
            self.assertTrue(mock_req.called)
            called_args, called_kwargs = mock_req.call_args
            payload = called_kwargs.get('payload') or called_args[1]

            self.assertEqual(payload.get('line_items[0][price]'), 'price_abc_123')
            self.assertEqual(payload.get('metadata[odoo_order_id]'), str(self.order.id))
            self.assertEqual(payload.get('subscription_data[metadata][odoo_order_id]'), str(self.order.id))
            self.assertEqual(payload.get('subscription_data[metadata][odoo_order_name]'), self.order.name or "")

            expected_desc = "%s - 3 cuotas de 100.0 %s (Total: 300.0 %s)" % (
                self.order.name or "",
                self.order.currency_id.name or "EUR",
                self.order.currency_id.name or "EUR"
            )
            self.assertEqual(payload.get('subscription_data[description]'), expected_desc)
            self.assertTrue('subscription_data[cancel_at]' in payload)

    def test_07_sync_invoice_fallback_mechanism(self):
        """Test that _sync_invoice_paid fetches the subscription from Stripe API as a fallback when not found locally."""
        from unittest.mock import patch

        # Make sure the order has NO stripe subscription linked
        self.order.write({
            'stripe_subscription_id': False,
            'stripe_subscription_ref': False,
        })

        # Create schedule line that is unpaid
        schedule = self.env['sale.subscription.schedule'].create({
            'order_id': self.order.id,
            'date_due': '2026-06-25',
            'date_schedule': '2026-06-25',
            'payment_state': 'not_paid',
            'amount_recurring_taxinc': 100.0
        })

        provider_vals = {
            'name': 'Stripe',
            'code': 'stripe',
            'state': 'test',
            'stripe_publishable_key': 'pk_test_mock',
            'stripe_secret_key': 'sk_test_mock',
        }
        provider = self.env['payment.provider'].sudo().search([
            ('code', '=', 'stripe'),
        ], limit=1)
        if not provider:
            provider = self.env['payment.provider'].create(provider_vals)
        else:
            provider.write(provider_vals)

        sub_payload = {
            'id': 'sub_fallback_999',
            'customer': 'cus_test_123',
            'status': 'active',
            'current_period_start': 1716654873,
            'current_period_end': 1719333273,
            'metadata': {
                'odoo_order_id': str(self.order.id)
            },
            'items': {
                'data': [{
                    'price': {
                        'id': 'price_fallback_abc',
                        'product': 'prod_fallback_xyz',
                        'unit_amount': 10000,
                        'currency': 'eur',
                        'recurring': {
                            'interval': 'month'
                        }
                    }
                }]
            }
        }

        # Mock Stripe API get subscription request
        with patch.object(type(provider), '_stripe_make_request') as mock_req:
            mock_req.return_value = sub_payload

            # Trigger invoice.paid webhook for sub_fallback_999
            invoice_payload = {
                'id': 'in_fallback_123',
                'subscription': 'sub_fallback_999',
                'status': 'paid',
                'amount_paid': 10000
            }

            self.env['stripe.sync']._sync_invoice_paid(invoice_payload)

            # Verify the API was called to get subscription
            mock_req.assert_any_call("subscriptions/sub_fallback_999", method='GET')

            # Verify subscription and order were successfully linked and the schedule is now paid!
            self.order.refresh()
            self.assertTrue(self.order.stripe_subscription_id)
            self.assertEqual(self.order.stripe_subscription_ref, 'sub_fallback_999')
            self.assertEqual(schedule.payment_state, 'paid')
