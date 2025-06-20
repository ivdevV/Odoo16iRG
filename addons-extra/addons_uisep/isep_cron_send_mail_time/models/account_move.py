# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'


    def send_template_link_payment_massive_for_time(self):

        num_day_time = int(self.env['ir.config_parameter'].sudo().get_param('num_day_time'))

        today = fields.Date.today()
        today_start = datetime.combine(today, datetime.min.time())
        seven_days_ago_start = today_start - timedelta(days=num_day_time)
        seven_days_ago_end = seven_days_ago_start + timedelta(days=1)

        mail_message_env = self.env['mail.message'].sudo().search([
            ('model', '=', 'account.move'),
            ('subject', '=', 'Link de Pago de Suscripcion Factura'),
            ('create_date', '>=', seven_days_ago_start),
            ('create_date', '<', seven_days_ago_end),

            ], order='create_date desc')

        latest_messages = {}
        for message in mail_message_env:
            res_id = message.res_id
            if res_id not in latest_messages or message.create_date > latest_messages[res_id].create_date:
                latest_messages[res_id] = message


        account_move_records = self.search([
            ('state', '=', 'posted'),
            ('move_type', '=', 'out_invoice'),
            ('payment_state', 'in', ['not_paid', 'partial'])
            ])
            
        for account_move in account_move_records:
            if account_move.id in latest_messages:
                self.send_mail_pay(account_move)
        


    def send_mail_pay(self, invoice):
        template_id = self.env.ref('isep_sale_order_cron_payment.link_card_email_template_invoice').id
        template = self.env['mail.template'].sudo().browse(template_id)

        email_values = template.generate_email(invoice.id, ['body_html', 'subject', 'email_to', 'email_from'])
        email_body = email_values.get('body_html')
        subject = email_values.get('subject')
        email_to = email_values.get('email_to')
        email_from = email_values.get('email_from')

        template.sudo().send_mail(invoice.id, force_send=True)

        invoice.message_post(
            body=email_body,
            subject=subject,
            message_type='email',
            subtype_id=self.env.ref('mail.mt_comment').id,
            email_from=email_from,
            email_to=email_to
        )