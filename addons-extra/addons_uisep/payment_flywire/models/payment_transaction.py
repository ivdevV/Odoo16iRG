import time
import logging
import pprint

from werkzeug import urls

from odoo import _, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_flywire.controllers.main import FlywireController
import requests

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _flywire_make_redirect(self, reference):
        reference = reference.get('reference')
        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'flywire')] , limit=1)
        _logger.info("payload:\n%s" % str(tx))
        if tx:
            base_url = tx.provider_id.get_base_url()
            partner_first_name, partner_last_name = payment_utils.split_partner_name(tx.partner_name)
            webhook_url = urls.url_join(base_url, FlywireController._webhook_url)
            return_url = f'{urls.url_join(base_url, FlywireController._return_url)}' \
                            f'?reference={urls.url_quote_plus(tx.reference)}'
            flywire_provider = False
            flywire_payment_destination = False

            for line in  tx.provider_id.flywire_portal_ids:
                if line.currency_id == tx.currency_id:
                    flywire_provider = line.flywire_provider
                    flywire_payment_destination = line.flywire_payment_destination
                    break
            if not flywire_provider or not flywire_payment_destination:
                raise UserError('Divisa no no disponible')

            if  tx.currency_id not in tx.provider_id.flywire_portal_ids.mapped('currency_id'):
                raise UserError('Divisa no disponible.')

            if not tx.partner_email:
                raise UserError('El correo del cliente es requerido.')
            """ if not tx.partner_address:
                raise UserError('La dirección del cliente es requerido.')
            if not tx.partner_city:
                raise UserError('La ciudad del cliente es requerido.')
            if not tx.partner_state_id:
                raise UserError('El estado (Dirección) del cliente es requerido.')
            if not tx.partner_zip:
                raise UserError('El codigo ZIP del cliente es requerido.')
            if not tx.partner_phone:
                raise UserError('El número de teléfono del cliente es requerido.')"""
            
            client = False
            if tx.sale_order_ids:
                for line in tx.sale_order_ids:
                    client = line.partner_id
                    if line.partner_invoice_id:
                        client = line.partner_id
                    break       

            if not client:
                for line in tx.invoice_ids:
                    client = line.partner_id
                    break    

                            

            payload = {
                    "provider": flywire_provider,
                    "payment_destination": flywire_payment_destination,
                    "country": tx.partner_country_id.code,
                    "amount": int(tx.amount*100), # ok
                    "return_cta": urls.url_join(base_url, FlywireController._return_url), # ok
                    "return_cta_name": "Regresar a Universidad ISEP", # ok
                    "sender_email": client.email or 'cobranza@universidadisep.com',
                    "sender_first_name": client.name or  'Nombre',
                    "sender_last_name": client.name or  'Apellidos' ,
                    "sender_address1": client.street or  'Direccion' ,
                    "sender_city": client.city or  'Ciudad',
                    "sender_state": client.state_id.name  or 'Estado',
                    "sender_zip": client.zip or "00000",
                    "sender_phone": client.phone or "523334008005",
                    "dynamic_fields": {
                        "student_id": str(client.id).zfill(8),                    
                    },
                    "callback_id": tx.reference,
                    "callback_version": "2",
                    "callback_url": webhook_url,
                    "return_url": return_url,
                    # "recurringType": "tokenization",
                }
            # "amount_from": int(tx.amount*100),
            #"currency_from": tx.currency_id.name,
            #"currency_to": tx.currency_id.name,

            
            _logger.info("*******************************************")
            _logger.info("*******************************************")
            _logger.info("payload:\n%s", pprint.pformat(payload))

            endpoint = tx.provider_id._flywire_get_api_url()        
            flywire_url = tx.provider_id._flywire_make_request(endpoint, payload=payload)['url']

            return flywire_url
        else:
            return ''

        """
        "dynamic_fields": {
                    "student_id": "123456",
                    "student_first_name": "John",
                    "student_last_name": "Doe"
                }
        """

    def _get_specific_rendering_values(self, processing_values):        
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'flywire':
            return res

        rendering_values = {
            'api_url': '%s%s%s' % (FlywireController._redirect_url,'?reference=',self.reference),            
        }

        return rendering_values

    
    def _get_tx_from_return_status_flywire(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on flywire data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        _logger.info("*******************************************")
        _logger.info("*******************************************")
        _logger.info("notification_data:\n%s", str(notification_data) )

        reference = notification_data.get('reference')
        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'flywire')])
        if not tx:
            raise ValidationError(
                "flywire: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on flywire data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        _logger.info("*******************************************")
        _logger.info("*******************************************")
        _logger.info("notification_data:\n%s", str(notification_data) )
        
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'flywire' or len(tx) == 1:
            return tx

        reference = notification_data.get('data').get('external_reference')
        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'flywire')])
        if not tx:
            raise ValidationError(
                "flywire: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        """ Override of payment to process the transaction based on flywire data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != 'flywire':
            return

        txn_id = notification_data.get('data').get('payment_id')
        txn_type = notification_data.get('event_type')
        if not all((txn_id, txn_type)):
            raise ValidationError(
                "flywire: " + _(
                    "Missing value for txn_id (%(txn_id)s) or txn_type (%(txn_type)s).",
                    txn_id=txn_id, txn_type=txn_type
                )
            )
        self.provider_reference = txn_id

        payment_status = notification_data.get('event_type')
        data=notification_data.get('data')
        if payment_status in ['initiated','processed']:
            self._set_pending(state_message=payment_status)
        elif payment_status in ['delivered','guaranteed']:
            self._set_done()
        elif payment_status in ['failed']:
            self._set_canceled("Flywire: Status failed: %s", data.get('reason'))
        elif payment_status in ['cancelled']:
            self._set_canceled("Flywire: Status cancelled: %s", data.get('cancellation_reason'))
            
        else:
            _logger.info(
                "received data with invalid payment status (%s) for transaction with reference %s",
                payment_status, self.reference
            )
            self._set_error(
                "flywire: " + _("Received data with invalid payment status: %s", payment_status)
            )

