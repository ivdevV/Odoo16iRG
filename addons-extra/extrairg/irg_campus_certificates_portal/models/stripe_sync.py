# -*- coding: utf-8 -*-
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class StripeSync(models.AbstractModel):
    _inherit = 'stripe.sync'

    @api.model
    def _sync_checkout_session(self, session_obj):
        """
        Extender checkout.session.completed para procesar pagos de certificados.
        """
        metadata = session_obj.get('metadata', {}) or {}
        cert_req_id = metadata.get('certificate_request_id')
        if cert_req_id:
            _logger.info("Stripe Webhook: procesando Checkout Session completada para Certificado ID %s", cert_req_id)
            cert_req = self.env['irg.certificate.request'].sudo().browse(int(cert_req_id))
            if cert_req.exists():
                cert_req._process_stripe_checkout_payment(session_obj)
                # Vincular el customer id si corresponde
                customer_id = session_obj.get('customer')
                partner = cert_req.partner_id
                if partner and customer_id and not partner.stripe_customer_id:
                    partner.write({'irg_stripe_customer_id': customer_id})
                return
        super(StripeSync, self)._sync_checkout_session(session_obj)
