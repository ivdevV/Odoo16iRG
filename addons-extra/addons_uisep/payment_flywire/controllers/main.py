# -*- coding: utf-8 -*-
import logging
import pprint

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request
import json
import werkzeug

_logger = logging.getLogger(__name__)



class FlywireController(http.Controller):
    _return_url = '/payment/flywire/return'
    _webhook_url = '/payment/flywire/webhook'
    _redirect_url = '/payment/flywire/redirect'


    @http.route(_redirect_url, type='http', auth='public', methods=['POST'] , csrf=False, save_session=False)
    def flywiret_redirect_url(self, **reference):
        flywire_url = request.env['payment.transaction'].sudo()._flywire_make_redirect(reference)
        _logger.info('********** REFERENCE: %s' % pprint.pformat(reference))  # debug
        _logger.info('********** URL: %s' % flywire_url)  # debug
        _logger.info("*******************************************")
        _logger.info("*******************************************")
        return werkzeug.utils.redirect(flywire_url)

    # @http.route(_return_url, type='http', auth='public', methods=['GET'])
    @http.route(_return_url, type='http', auth='public',  csrf=False, save_session=False)
    def flywire_return_from_checkout(self, **data):
        _logger.info("*******************************************")
        _logger.info("*******************************************")
        _logger.info("RETURN data:\n%s", pprint.pformat(data))
        _logger.info("RETURN data:\n%s", pprint.pformat(data))
        _logger.info("RETURN data:\n%s", pprint.pformat(data))
        _logger.info("*******************************************")
        _logger.info("*******************************************")

        # Check the integrity of the notification
        #tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_return_status_flywire(
        #    'flywire', data
        #)
        # self._verify_notification_signature(data, tx_sudo)

        # Handle the notification data
        # tx_sudo._handle_notification_data('flywire', data)
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type="json" , auth='public')
    def flywire_webhook(self):
        data = json.loads(request.httprequest.data)
        _logger.info("*******************************************")
        _logger.info("*******************************************")
        _logger.info("notification received from flywire with data:\n%s", pprint.pformat(data))
        _logger.info("*******************************************")
        _logger.info("*******************************************")
        """
        {'data': {'amount_from': '800',
                'amount_to': '3602',
                'country': 'PE',
                'currency_from': 'PEN',
                'currency_to': 'MXN',
                'expiration_date': '2023-10-22T23:27:54Z',
                'external_reference': 'S00006-8',
                'fields': {'enrollment_id': None,
                            'payment_type': None,
                            'payment_type_other': None,
                            'student_email': None,
                            'student_first_name': None,
                            'student_id': '232131321321',
                            'student_last_name': None},
                'payment_id': 'IUS516514823',
                'payment_method': {'type': 'card'},
                'status': 'initiated'},
        'event_date': '2023-10-20T23:27:54Z',
        'event_resource': 'payments',
        'event_type': 'initiated'}

        """
        try:
            # Check the origin and integrity of the notification
            tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                'flywire', data
            )

            # Handle the notification data
            tx_sudo._handle_notification_data('flywire', data)
        except ValidationError:  # Acknowledge the notification to avoid getting spammed
            _logger.exception("unable to handle the notification data; skipping to acknowledge")

        return 'SUCCESS'  # Acknowledge the notification


        