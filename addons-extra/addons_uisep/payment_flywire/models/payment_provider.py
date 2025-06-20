# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import hmac
import logging
import pprint
import requests
import six
from werkzeug.urls import url_join
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)

class PaymentProviderFlywire(models.Model):
    _name = 'payment.provider.flywire'

    flywire_provider = fields.Char(default="IUS", string="Provider",
        required='flywire',
    )

    flywire_payment_destination = fields.Char(default="isepmx", string="Payment Destination",
        required='flywire', 
    )
    currency_id = fields.Many2one('res.currency', required=True)

    provider_id = fields.Many2one('payment.provider', ondelete="cascade")


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('flywire', "flywire")], ondelete={'flywire': 'set default'}
    )
    
    
    flywire_portal_ids = fields.One2many('payment.provider.flywire', 'provider_id', string="Portales" )
    
    
    flywire_shared_secret = fields.Char(default="MN52UHpRNm7L2Usw9yhpCMqT", string="Shared Secret",
        required_if_provider='flywire',
    )

    @api.onchange('state')
    def onchange_is_published(self):
        if self.state == 'test' and self.code == 'Flywire':
            self.is_published == True



    def _flywire_get_api_url(self):
        self.ensure_one()

        if self.state == 'enabled':
            return 'https://gateway.flywire.com/v1/transfers.json'
        else:
            return 'https://gateway.demo.flywire.com/v1/transfers.json'
    
    def _flywire_get_api_token(self):
        """ Para cobrar un token, debe enviar una solicitud al punto de conexión de cargo. 
        La dirección URL de este punto de conexión varía según el entorno.POST
        Environment	URL
        Demo	https://checkout-api.demo.flywire.com/rest/payor/charge
        Prod	https://checkout-api.flywire.com/rest/payor/charge"""

        self.ensure_one()
        if self.state == 'enabled':
            return 'https://checkout-api.flywire.com/rest/payor/charge'
        else:
            return 'https://checkout-api.demo.flywire.com/rest/payor/charge'


    
    

    def _flywire_make_request(self, endpoint, payload=None, method='POST'):
        self.ensure_one()

        url = endpoint
        headers = {'Authorization': f'Bearer {self.flywire_shared_secret}'}
        try:
            if method == 'GET':
                response = requests.get(url, params=payload, headers=headers, timeout=10)
            else:
                response = requests.post(url, json=payload, timeout=10)
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError:
                    _logger.exception(
                        "Peticion invalida con data:\n%s", url, pprint.pformat(payload),
                    )
                    response_content = response.json()
                    error_message = response_content.get('errors')
                    raise ValidationError("Flywire -> Mensaje de error: '%s' " % error_message)
                    
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("No se pudo realizar la peticion en %s", url)
            raise ValidationError(
                "Flywire: " + _("Conexcion no establecida con el servicio de Flywire.")
            )
        return response.json()

