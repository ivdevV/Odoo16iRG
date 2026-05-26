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
        self.order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'is_subscription': True,
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
