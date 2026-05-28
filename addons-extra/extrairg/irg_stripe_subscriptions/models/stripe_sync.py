# -*- coding: utf-8 -*-
import json
import logging
from datetime import datetime
from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)


class StripeSync(models.AbstractModel):
    _name = 'stripe.sync'
    _description = 'Servicio de Sincronización Stripe'

    @api.model
    def _get_stripe_provider(self):
        """Devuelve el proveedor de Stripe activo."""
        provider = self.env['payment.provider'].sudo().search([
            ('code', '=', 'stripe'),
            ('state', 'in', ('enabled', 'test'))
        ], limit=1)
        return provider

    @api.model
    def dispatch_event(self, event_data):
        """Despacha el evento recibido desde el webhook al método correspondiente."""
        event_type = event_data.get('type')
        event_obj = event_data.get('data', {}).get('object', {})
        
        _logger.info("Despachando evento Stripe de tipo: %s", event_type)
        
        if event_type in ('customer.subscription.created', 'customer.subscription.updated'):
            self._sync_subscription_object(event_obj)
        elif event_type == 'customer.subscription.deleted':
            self._sync_subscription_deleted(event_obj)
        elif event_type == 'checkout.session.completed':
            self._sync_checkout_session(event_obj)
        elif event_type in ('invoice.paid', 'invoice.payment_succeeded'):
            self._sync_invoice_paid(event_obj)
        elif event_type == 'invoice.payment_failed':
            self._sync_invoice_payment_failed(event_obj)
        elif event_type == 'payment_intent.succeeded':
            self._sync_payment_intent_succeeded(event_obj)
        else:
            _logger.info("Evento Stripe '%s' no requiere acción de sincronización directa.", event_type)

    @api.model
    def _extract_subscription_id_from_invoice(self, invoice_obj):
        """Obtiene el ID de suscripcion desde distintas versiones del payload de Invoice."""
        subscription = invoice_obj.get('subscription')
        if isinstance(subscription, dict):
            subscription = subscription.get('id')
        if subscription:
            return subscription

        parent = invoice_obj.get('parent') or {}
        subscription_details = parent.get('subscription_details') or invoice_obj.get('subscription_details') or {}
        subscription = subscription_details.get('subscription')
        if isinstance(subscription, dict):
            subscription = subscription.get('id')
        if subscription:
            return subscription

        lines = invoice_obj.get('lines', {}).get('data', [])
        for line in lines:
            subscription = line.get('subscription')
            if isinstance(subscription, dict):
                subscription = subscription.get('id')
            if subscription:
                return subscription
            line_parent = line.get('parent') or {}
            line_details = line_parent.get('subscription_item_details') or line_parent.get('subscription_details') or {}
            subscription = line_details.get('subscription')
            if isinstance(subscription, dict):
                subscription = subscription.get('id')
            if subscription:
                return subscription
        return False

    @api.model
    def _fetch_invoice_from_stripe(self, invoice_id):
        if not invoice_id:
            return {}
        provider = self._get_stripe_provider()
        if not provider:
            return {}
        try:
            invoice = provider._stripe_make_request(f"invoices/{invoice_id}", method='GET')
            return invoice if invoice and not invoice.get('error') else {}
        except Exception:
            _logger.warning("No se pudo recuperar la factura %s desde Stripe", invoice_id)
            return {}

    @api.model
    def _amount_from_stripe_minor_units(self, amount, currency):
        if amount is None:
            return 0.0
        decimal_places = currency.decimal_places if currency else 2
        return amount / float(10 ** decimal_places)

    @api.model
    def _register_paid_invoice_on_schedule(self, order, schedule, invoice_obj):
        """Registra el pago externo de Stripe en el plazo para disparar los computes nativos."""
        invoice_id = invoice_obj.get('id')
        paid_amount = self._amount_from_stripe_minor_units(
            invoice_obj.get('amount_paid') or invoice_obj.get('amount_received'),
            order.currency_id,
        )
        if not paid_amount:
            paid_amount = schedule.amount_recurring_taxinc
        paid_amount = min(paid_amount, schedule.amount_recurring_taxinc)

        legacy_obj = self.env['sale.note.inv.legacy'].sudo()
        legacy = legacy_obj.search([
            ('schedule_id', '=', schedule.id),
            ('name', '=', invoice_id or 'Stripe'),
        ], limit=1)

        legacy_vals = {
            'name': invoice_id or 'Stripe',
            'schedule_id': schedule.id,
            'note': 'Pago registrado automaticamente desde Stripe.',
            'invoice_date': fields.Date.context_today(self),
            'payment_date': fields.Date.context_today(self),
            'amount_total_invoice': schedule.amount_recurring_taxinc,
            'amount_total_payment': paid_amount,
        }
        if legacy:
            legacy.write(legacy_vals)
        else:
            legacy_obj.create(legacy_vals)

        schedule.invalidate_recordset(['total_invoiced', 'total_paid', 'total_residual', 'payment_state'])
        schedule._compute_total_invoiced()
        schedule.compute_payment_state()
        order.invalidate_recordset(['amount_due_total'])
        order._compute_amount_due_total()

        next_unpaid = order.subscription_schedule.filtered(
            lambda line: line.payment_state != 'paid'
        ).sorted('date_due')[:1]
        order_vals = {
            'next_invoice_date': next_unpaid.date_due if next_unpaid else False,
        }
        if invoice_id:
            order_vals.update({
                'stripe_last_paid_invoice_id': invoice_id,
                'stripe_invoice_id': invoice_id,
            })
        order.sudo().write(order_vals)

    @api.model
    def _find_partner(self, customer_id, email=False):
        """
        Busca al partner en Odoo con prioridad:
        1. stripe_customer_id ya asignado.
        2. metadata.odoo_partner_id consultando al API de Stripe para el Customer.
        3. Email exacto.
        """
        partner_obj = self.env['res.partner'].sudo()
        if not customer_id:
            return partner_obj

        # 1. Buscar por stripe_customer_id
        partner = partner_obj.search(['|', ('stripe_customer_id', '=', customer_id), ('irg_stripe_customer_id', '=', customer_id)], limit=1)
        if partner:
            return partner

        # 2. Consultar la API de Stripe
        provider = self._get_stripe_provider()
        if provider:
            try:
                res = provider._stripe_make_request(f"customers/{customer_id}", method='GET')
                if res and not res.get('error'):
                    odoo_partner_id = res.get('metadata', {}).get('odoo_partner_id')
                    if odoo_partner_id:
                        partner = partner_obj.browse(int(odoo_partner_id)).exists()
                        if partner:
                            partner.write({'irg_stripe_customer_id': customer_id})
                            return partner
                    
                    # Si no hay metadata, intentamos obtener el email del customer devuelto
                    if not email:
                        email = res.get('email')
            except Exception:
                _logger.warning("No se pudo obtener el Customer %s de la API de Stripe", customer_id)

        # 3. Buscar por email exacto
        if email:
            partner = partner_obj.search([('email', '=ilike', email.strip())], limit=1)
            if partner:
                partner.write({'irg_stripe_customer_id': customer_id})
                return partner

        return partner_obj

    @api.model
    def _sync_subscription_object(self, sub_obj):
        """Sincroniza un objeto de suscripción de Stripe con stripe.subscription y sale.order."""
        stripe_id = sub_obj.get('id')
        customer_id = sub_obj.get('customer')
        status = sub_obj.get('status')
        metadata = sub_obj.get('metadata', {})
        
        _logger.info("Sincronizando suscripción Stripe: %s (Estado: %s)", stripe_id, status)
        
        # Buscar al partner
        partner = self._find_partner(customer_id)
        
        # Buscar o crear la suscripción local
        subscription = self.env['stripe.subscription'].sudo()._find_or_create_from_stripe_id(
            stripe_id, partner_id=partner.id if partner else False
        )

        # Extraer fechas
        start_ts = sub_obj.get('current_period_start')
        end_ts = sub_obj.get('current_period_end')
        current_period_start = fields.Datetime.to_string(datetime.utcfromtimestamp(start_ts)) if start_ts else False
        current_period_end = fields.Datetime.to_string(datetime.utcfromtimestamp(end_ts)) if end_ts else False

        # Extraer precio y producto
        items = sub_obj.get('items', {}).get('data', [])
        price_id = False
        product_id = False
        amount = 0.0
        currency_id = False
        interval = False

        if items:
            price_obj = items[0].get('price', {})
            price_id = price_obj.get('id')
            product_id = price_obj.get('product')
            
            # Importe y moneda
            unit_amount = price_obj.get('unit_amount', 0)
            amount = unit_amount / 100.0 if unit_amount else 0.0
            
            currency_code = price_obj.get('currency', 'eur').upper()
            currency = self.env['res.currency'].sudo().search([('name', '=', currency_code)], limit=1)
            currency_id = currency.id if currency else False
            
            interval = price_obj.get('recurring', {}).get('interval')

        # Última factura
        latest_invoice = sub_obj.get('latest_invoice')
        latest_invoice_id = latest_invoice if isinstance(latest_invoice, str) else (latest_invoice or {}).get('id')

        # Actualizar campos locales
        name = f"Suscripción {stripe_id}"
        if partner:
            name = f"Sub - {partner.name} [{stripe_id}]"

        subscription.write({
            'name': name,
            'partner_id': partner.id if partner else False,
            'status': status,
            'current_period_start': current_period_start,
            'current_period_end': current_period_end,
            'cancel_at_period_end': sub_obj.get('cancel_at_period_end', False),
            'price_id': price_id,
            'product_id': product_id,
            'amount': amount,
            'currency_id': currency_id,
            'interval': interval,
            'latest_invoice_id': latest_invoice_id,
            'metadata_json': json.dumps(metadata),
            'raw_payload': json.dumps(sub_obj),
        })

        # Buscar el sale.order asociado
        odoo_order_id = metadata.get('odoo_order_id')
        order = self.env['sale.order'].sudo()
        if odoo_order_id:
            order = order.browse(int(odoo_order_id)).exists()
        
        if not order:
            # Buscar por stripe_subscription_id o por stripe_subscription_ref
            order = self.env['sale.order'].sudo().search([
                '|',
                ('stripe_subscription_id', '=', subscription.id),
                ('stripe_subscription_ref', '=', stripe_id)
            ], limit=1)

        if order:
            # Vincular suscripción a la orden si no está vinculada
            order_vals = {}
            if order.stripe_subscription_id != subscription:
                order_vals['stripe_subscription_id'] = subscription.id
            if order.stripe_subscription_ref != stripe_id:
                order_vals['stripe_subscription_ref'] = stripe_id
            
            if order_vals:
                order.write(order_vals)

            # Sincronización de Estado con Odoo
            status_map = {
                'active': 'active',
                'trialing': 'active',
                'past_due': 'past_due',
                'paused': 'paused',
                'canceled': 'canceled',
                'unpaid': 'past_due',
                'incomplete': 'draft',
                'incomplete_expired': 'canceled',
            }
            new_state = status_map.get(status, 'active')
            
            if order.stripe_subscription_state != new_state:
                # Actualizar estado y registrar en chatter
                order._irg_mark_stripe_event(
                    event_name=f'webhook.subscription.updated({status})',
                    state=new_state
                )
                
                # Ejecutar acciones asociadas de pausa/resumen si procede
                if new_state == 'paused' and not order.subscription_suspended:
                    order.sudo().write({'subscription_suspended': True})
                    order.message_post(body=_("⏸️ Suscripción pausada en Odoo debido a evento en Stripe."))
                elif new_state == 'active' and order.subscription_suspended:
                    order.sudo().write({'subscription_suspended': False, 'stripe_grace_until': False})
                    order.message_post(body=_("▶️ Suscripción reactivada en Odoo debido a evento en Stripe."))
                elif new_state == 'canceled':
                    order.sudo().write({'subscription_suspended': True, 'to_renew': False})
                    order.message_post(body=_("🛑 Suscripción cancelada en Odoo debido a evento en Stripe."))
        
        return subscription

    @api.model
    def _sync_subscription_deleted(self, sub_obj):
        """Sincroniza la cancelación de una suscripción en Stripe."""
        stripe_id = sub_obj.get('id')
        _logger.info("Procesando evento de cancelación de suscripción Stripe: %s", stripe_id)
        
        # Actualizar el registro local
        subscription = self.env['stripe.subscription'].sudo().search([('stripe_id', '=', stripe_id)], limit=1)
        if subscription:
            subscription.write({
                'status': 'canceled',
                'raw_payload': json.dumps(sub_obj)
            })

        # Cancelar / suspender suscripción nativa asociada
        order = self.env['sale.order'].sudo().search([
            '|',
            ('stripe_subscription_id', '=', subscription.id if subscription else False),
            ('stripe_subscription_ref', '=', stripe_id)
        ], limit=1)

        if order:
            order._irg_mark_stripe_event(
                event_name='webhook.customer.subscription.deleted',
                state='canceled'
            )
            # Marcar como suspendida y desactivar renovación
            order.sudo().write({
                'subscription_suspended': True,
                'to_renew': False
            })
            order.message_post(body=_("🛑 <b>Suscripción cancelada automáticamente.</b> Evento 'customer.subscription.deleted' recibido desde Stripe."))

    @api.model
    def _sync_checkout_session(self, session_obj):
        """Sincroniza una sesión de Checkout completada desde Stripe."""
        session_id = session_obj.get('id')
        customer_id = session_obj.get('customer')
        client_ref = session_obj.get('client_reference_id', '')
        metadata = session_obj.get('metadata', {})
        stripe_sub_id = session_obj.get('subscription')
        payment_link_id = session_obj.get('payment_link')

        _logger.info(
            "Sincronizando Checkout Session completada: %s (Client Ref: %s)",
            session_id, client_ref
        )

        partner = self.env['res.partner'].sudo()
        order = self.env['sale.order'].sudo()

        # Identificar Partner / Order por client_reference_id
        if client_ref:
            if client_ref.startswith('odoo_order_'):
                try:
                    order_id = int(client_ref.replace('odoo_order_', ''))
                    order = order.browse(order_id).exists()
                    if order:
                        partner = order.partner_id
                except Exception:
                    pass
            elif client_ref.startswith('odoo_partner_'):
                try:
                    partner_id = int(client_ref.replace('odoo_partner_', ''))
                    partner = partner.browse(partner_id).exists()
                except Exception:
                    pass

        # Si no se identificó por client_reference_id, intentamos por metadata
        if not order and metadata.get('odoo_order_id'):
            order = order.browse(int(metadata.get('odoo_order_id'))).exists()
            if order and not partner:
                partner = order.partner_id

        if not partner and metadata.get('odoo_partner_id'):
            partner = partner.browse(int(metadata.get('odoo_partner_id'))).exists()

        # Si aún no tenemos partner, buscamos por customer_id
        if not partner and customer_id:
            partner = self._find_partner(customer_id)

        # Vincular stripe_customer_id al partner si no lo tiene
        if partner and customer_id and partner.stripe_customer_id != customer_id:
            partner.write({'irg_stripe_customer_id': customer_id})

        # Sincronizar el Payment Link si la sesión se originó desde uno
        if payment_link_id:
            provider = self._get_stripe_provider()
            if provider:
                try:
                    plink_res = provider._stripe_make_request(f"payment_links/{payment_link_id}", method='GET')
                    if plink_res and not plink_res.get('error'):
                        self._sync_payment_link_object(plink_res, partner=partner, order=order)
                except Exception:
                    _logger.warning("No se pudo obtener el Payment Link %s de Stripe", payment_link_id)

        # Sincronizar la suscripción si se generó una
        if stripe_sub_id:
            provider = self._get_stripe_provider()
            if provider:
                try:
                    sub_res = provider._stripe_make_request(f"subscriptions/{stripe_sub_id}", method='GET')
                    if sub_res and not sub_res.get('error'):
                        update_payload = {}
                        
                        # Si encontramos la orden, inyectamos odoo_order_id en los metadatos si no los tenía
                        if order and 'odoo_order_id' not in sub_res.get('metadata', {}):
                            update_payload["metadata[odoo_order_id]"] = str(order.id)
                            update_payload["metadata[odoo_order_name]"] = order.name or ""
                            
                        # Si la orden asociada tiene configurado 'end_date', calcula el timestamp de cancelación
                        if order and order.end_date:
                            import datetime as dt_mod
                            import time
                            if isinstance(order.end_date, dt_mod.datetime):
                                end_dt = order.end_date
                            else:
                                end_dt = dt_mod.datetime.combine(order.end_date, dt_mod.time.min)
                            cancel_at_ts = int(time.mktime(end_dt.timetuple()))
                            update_payload["cancel_at"] = str(cancel_at_ts)
                            
                        if update_payload:
                            try:
                                provider._stripe_make_request(
                                    f"subscriptions/{stripe_sub_id}",
                                    payload=update_payload
                                )
                                if "metadata[odoo_order_id]" in update_payload:
                                    sub_res.setdefault('metadata', {})
                                    sub_res['metadata']['odoo_order_id'] = str(order.id)
                                    sub_res['metadata']['odoo_order_name'] = order.name or ""
                                if "cancel_at" in update_payload:
                                    sub_res['cancel_at'] = int(update_payload["cancel_at"])
                                    sub_res['cancel_at_period_end'] = True
                            except Exception:
                                _logger.exception("Error updating subscription %s in Stripe", stripe_sub_id)
                        
                        # Sincronizamos la suscripción
                        self._sync_subscription_object(sub_res)
                except Exception:
                    _logger.warning("No se pudo obtener la suscripción %s de Stripe para sincronización", stripe_sub_id)

    @api.model
    def _sync_payment_link_object(self, plink_obj, partner=False, order=False):
        """Sincroniza un Payment Link de Stripe localmente."""
        plink_id = plink_obj.get('id')
        url = plink_obj.get('url')
        active = plink_obj.get('active', True)
        metadata = plink_obj.get('metadata', {})
        
        # Buscar precio
        price_id = False
        line_items = plink_obj.get('line_items', {}).get('data', [])
        if not line_items:
            # A veces Stripe no devuelve line_items en el webhook simple, pero sí en una consulta directa.
            # Dejamos opcional.
            pass
        else:
            price_id = line_items[0].get('price', {}).get('id')

        vals = {
            'name': f"Enlace de pago {plink_id}",
            'stripe_id': plink_id,
            'url': url,
            'active': active,
            'price_id': price_id,
            'metadata_json': json.dumps(metadata),
        }
        
        link_rec = self.env['stripe.payment.link'].sudo()._find_or_create_from_stripe_id(plink_id, vals)

        # Vincular clientes y órdenes
        if partner:
            partner.sudo().write({
                'stripe_payment_link_ids': [(4, link_rec.id)]
            })
        if order:
            order.sudo().write({
                'stripe_payment_link_id': link_rec.id
            })
            
        return link_rec

    @api.model
    def _sync_invoice_paid(self, invoice_obj):
        """Procesa el cobro de una factura en Stripe, marcando el plazo correspondiente en Odoo como pagado."""
        invoice_id = invoice_obj.get('id')
        subscription_id = self._extract_subscription_id_from_invoice(invoice_obj)
        if not subscription_id and invoice_id:
            invoice_obj = self._fetch_invoice_from_stripe(invoice_id) or invoice_obj
            subscription_id = self._extract_subscription_id_from_invoice(invoice_obj)
        if not subscription_id:
            _logger.warning(
                "Stripe Webhook (sync): invoice.paid sin suscripcion identificable (invoice=%s).",
                invoice_id,
            )
            return
            
        # Buscamos la orden por la suscripción vinculada o referencia string
        order = self.env['sale.order'].sudo().search([
            '|',
            ('stripe_subscription_id.stripe_id', '=', subscription_id),
            ('stripe_subscription_ref', '=', subscription_id)
        ], limit=1)
        
        if not order:
            provider = self._get_stripe_provider()
            if provider:
                try:
                    sub_res = provider._stripe_make_request(f"subscriptions/{subscription_id}", method='GET')
                    if sub_res and not sub_res.get('error'):
                        metadata = sub_res.get('metadata', {})
                        odoo_order_id = metadata.get('odoo_order_id')
                        if odoo_order_id:
                            self._sync_subscription_object(sub_res)
                            order = self.env['sale.order'].sudo().browse(int(odoo_order_id)).exists()
                except Exception:
                    _logger.warning("No se pudo recuperar la suscripción %s desde Stripe para fallback en invoice.paid", subscription_id)

        if order:
            if invoice_id and order.stripe_last_paid_invoice_id == invoice_id:
                _logger.info(
                    "Stripe Webhook (sync): invoice.paid duplicado omitido para la orden %s (invoice=%s).",
                    order.name,
                    invoice_id,
                )
                return
            duplicated_legacy = order.subscription_schedule.mapped('payment_legacy_ids').filtered(
                lambda legacy: legacy.name == invoice_id
            ) if invoice_id else False
            if duplicated_legacy:
                _logger.info(
                    "Stripe Webhook (sync): invoice.paid ya registrado en cronograma para la orden %s (invoice=%s).",
                    order.name,
                    invoice_id,
                )
                order.sudo().write({'stripe_last_paid_invoice_id': invoice_id})
                return

            _logger.info("Stripe Webhook (sync): invoice.paid recibido para la orden %s (Sub: %s)", order.name, subscription_id)
            
            # Registrar evento en chatter
            order._irg_mark_stripe_event(
                event_name='invoice.paid',
                state='active',
                clear_grace=True
            )
            
            # Buscar el plazo del cronograma más antiguo sin pagar en Odoo
            unpaid = order.subscription_schedule.filtered(
                lambda s: s.payment_state != 'paid'
            ).sorted('date_due')
            
            if unpaid:
                self._register_paid_invoice_on_schedule(order, unpaid[0], invoice_obj)
                _logger.info(
                    "Stripe Webhook (sync): Plazo %s ('%s') marcado como pagado para orden %s debido a cobro en Stripe.",
                    unpaid[0].id, unpaid[0].name or unpaid[0].date_due, order.name
                )
            else:
                _logger.info("Stripe Webhook (sync): No hay plazos pendientes de pago para la orden %s.", order.name)

    @api.model
    def _sync_payment_intent_succeeded(self, payment_intent_obj):
        """Fallback para pagos de Stripe que llegan como payment_intent.succeeded."""
        invoice = payment_intent_obj.get('invoice')
        invoice_id = invoice.get('id') if isinstance(invoice, dict) else invoice
        if not invoice_id:
            _logger.info(
                "Stripe Webhook (sync): payment_intent.succeeded sin invoice asociado (%s).",
                payment_intent_obj.get('id'),
            )
            return
        invoice_obj = self._fetch_invoice_from_stripe(invoice_id)
        if invoice_obj:
            self._sync_invoice_paid(invoice_obj)

    @api.model
    def _sync_invoice_payment_failed(self, invoice_obj):
        """Procesa el fallo de cobro de una factura en Stripe, actualizando la orden de Odoo."""
        invoice_id = invoice_obj.get('id')
        subscription_id = self._extract_subscription_id_from_invoice(invoice_obj)
        if not subscription_id and invoice_id:
            invoice_obj = self._fetch_invoice_from_stripe(invoice_id) or invoice_obj
            subscription_id = self._extract_subscription_id_from_invoice(invoice_obj)
        if not subscription_id:
            _logger.warning(
                "Stripe Webhook (sync): invoice.payment_failed sin suscripcion identificable (invoice=%s).",
                invoice_id,
            )
            return
            
        order = self.env['sale.order'].sudo().search([
            '|',
            ('stripe_subscription_id.stripe_id', '=', subscription_id),
            ('stripe_subscription_ref', '=', subscription_id)
        ], limit=1)
        
        if not order:
            provider = self._get_stripe_provider()
            if provider:
                try:
                    sub_res = provider._stripe_make_request(f"subscriptions/{subscription_id}", method='GET')
                    if sub_res and not sub_res.get('error'):
                        metadata = sub_res.get('metadata', {})
                        odoo_order_id = metadata.get('odoo_order_id')
                        if odoo_order_id:
                            self._sync_subscription_object(sub_res)
                            order = self.env['sale.order'].sudo().browse(int(odoo_order_id)).exists()
                except Exception:
                    _logger.warning("No se pudo recuperar la suscripción %s desde Stripe para fallback en invoice.payment_failed", subscription_id)

        if order:
            from datetime import timedelta
            # Consultar días de gracia de la configuración
            grace_days = int(self.env['ir.config_parameter'].sudo().get_param('irg_stripe.overdue_grace_days', '15'))
            grace_until = fields.Date.today() + timedelta(days=grace_days)
            
            order._irg_mark_stripe_event(
                event_name='invoice.payment_failed',
                state='past_due',
                grace_until=grace_until
            )
            _logger.warning("Stripe Webhook (sync): Pago fallido recibido para orden %s (Sub: %s). Estado: past_due.", order.name, subscription_id)
