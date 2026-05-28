# -*- coding: utf-8 -*-
import json
import logging
import hmac
import hashlib
import time
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class StripeWebhookController(http.Controller):

    def _verify_stripe_signature(self, payload, sig_header, secret, tolerance=300):
        """Valida la firma HMAC-SHA256 del webhook de Stripe de forma nativa sin usar la librería stripe."""
        if not sig_header or not secret:
            return False
        
        try:
            pairs = [pair.split('=') for pair in sig_header.split(',')]
            sig_dict = {pair[0].strip(): pair[1].strip() for pair in pairs if len(pair) == 2}
        except Exception:
            return False
        
        timestamp = sig_dict.get('t')
        signature = sig_dict.get('v1')
        
        if not timestamp or not signature:
            return False
            
        try:
            ts_int = int(timestamp)
            now = int(time.time())
            if abs(now - ts_int) > tolerance:
                _logger.warning("Stripe Webhook: Firma expirada (timestamp: %s, actual: %s)", ts_int, now)
                return False
        except ValueError:
            return False
            
        if isinstance(payload, str):
            payload_bytes = payload.encode('utf-8')
        else:
            payload_bytes = payload
            
        signed_payload = f"{timestamp}.".encode('utf-8') + payload_bytes
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            signed_payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)

    @http.route('/stripe/webhook', type='http', auth='public', methods=['POST'], csrf=False)
    def stripe_webhook(self):
        payload = request.httprequest.data
        sig_header = request.httprequest.headers.get('Stripe-Signature')
        
        param_obj = request.env['ir.config_parameter'].sudo()
        webhook_secret = param_obj.get_param('stripe.webhook_secret')
        if not webhook_secret:
            provider = request.env['payment.provider'].sudo().search([
                ('code', '=', 'stripe'),
                ('state', 'in', ('enabled', 'test')),
            ], limit=1)
            webhook_secret = provider.stripe_webhook_secret if provider else False
        
        if not webhook_secret:
            _logger.error("Stripe Webhook: no hay secreto configurado en 'stripe.webhook_secret' ni en el proveedor Stripe.")
            return request.make_response("Webhook secret not configured", status=500)
            
        # Validar la firma nativamente
        if not self._verify_stripe_signature(payload, sig_header, webhook_secret):
            _logger.error("Stripe Webhook: Firma de Stripe inválida.")
            return request.make_response("Invalid signature", status=400)
            
        try:
            event = json.loads(payload)
        except Exception as e:
            _logger.error("Stripe Webhook: Payload JSON inválido. %s", str(e))
            return request.make_response("Invalid payload JSON", status=400)
            
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
            return request.make_response(f"Internal processing error: {str(e)}", status=500)
