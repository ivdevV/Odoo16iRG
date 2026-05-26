# -*- coding: utf-8 -*-
import json
import logging
try:
    import stripe
except ImportError:
    stripe = None

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class StripeWebhookController(http.Controller):

    @http.route('/stripe/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def stripe_webhook(self):
        if not stripe:
            _logger.error("Stripe Webhook: La librería de Python 'stripe' no está instalada en el sistema.")
            return request.make_response("Python stripe library not installed", status=500)

        payload = request.httprequest.data
        sig_header = request.httprequest.headers.get('Stripe-Signature')
        
        param_obj = request.env['ir.config_parameter'].sudo()
        webhook_secret = param_obj.get_param('stripe.webhook_secret')
        api_key = param_obj.get_param('stripe.api_key')
        api_version = param_obj.get_param('stripe.api_version')
        
        if not webhook_secret:
            _logger.error("Stripe Webhook: 'stripe.webhook_secret' no está configurado en los Parámetros del Sistema.")
            return request.make_response("Webhook secret not configured", status=500)
            
        if api_key:
            stripe.api_key = api_key
        if api_version:
            stripe.api_version = api_version
            
        try:
            # Validar firma del webhook
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            _logger.error("Stripe Webhook: Payload inválido. %s", str(e))
            return request.make_response("Invalid payload", status=400)
        except stripe.error.SignatureVerificationError as e:
            _logger.error("Stripe Webhook: Error de verificación de firma. %s", str(e))
            return request.make_response("Invalid signature", status=400)
        except Exception as e:
            _logger.error("Stripe Webhook: Error inesperado al validar firma. %s", str(e))
            return request.make_response("Verification error", status=400)
            
        event_id = event.get('id')
        event_type = event.get('type')
        
        # --- Control de Idempotencia ---
        log_obj = request.env['stripe.event.log'].sudo()
        existing_log = log_obj.search([('event_id', '=', event_id)], limit=1)
        if existing_log:
            _logger.info("Stripe Webhook: Evento %s ya procesado previamente (idempotencia). Omitiendo.", event_id)
            return request.make_response("Event already processed", status=200)
            
        # Creamos el registro del log de eventos
        payload_str = payload.decode('utf-8') if isinstance(payload, bytes) else str(payload)
        log_record = log_obj.create({
            'event_id': event_id,
            'event_type': event_type,
            'payload': payload_str,
            'processed': False,
        })
        
        # --- Despacho del Evento ---
        try:
            request.env['stripe.sync'].sudo().dispatch_event(event)
            log_record.write({
                'processed': True,
            })
            _logger.info("Stripe Webhook: Evento %s de tipo %s procesado con éxito.", event_id, event_type)
            return request.make_response("OK", status=200)
        except Exception as e:
            _logger.exception("Stripe Webhook: Error al procesar el evento %s", event_id)
            log_record.write({
                'error': str(e),
            })
            # Devolvemos un código 500 para indicar a Stripe que reintente en caso de fallo temporal
            return request.make_response(f"Internal processing error: {str(e)}", status=500)
