# -*- coding: utf-8 -*-
import logging
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    send_sign = fields.Boolean('Firma enviado', compute="_compute_send_sign")


    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('website_id'):
                recurrence_record = self.env['sale.temporal.recurrence'].search([
                    ('use_public_auto', '=', True)
                    ], limit=1)
                vals['recurrence_id'] = recurrence_record.id
                vals['start_date'] = fields.Date.today()

        return super().create(vals_list)



    def send_automated_action(self):

        today = datetime.now().strftime('%Y-%m-%d')


        records = self.env['sale.order'].search([
            ('state', 'in', ('done', 'sale')), 
            ('team_id.is_web', '=', True), 
            ('sign_id', '=', False),
            ('create_date', '>=', today + ' 00:00:00'),
            ('create_date', '<=', today + ' 23:59:59')
            ])

        for record in records:

            record.action_send_to_sign()

            sign_template = self.env['sign.template'].sudo().search([
                    ('sale_id', '=', record.id)
                    ], order='create_date desc', limit=1)

            sign_template.create_link_sign()

            self.send_mail_sign_website(record)

            


    
    def send_mail_sign_website(self, order):
        template_id = self.env.ref('isep_website_sale_custom.link_sign_website_template_sale_order').id
        template = self.env['mail.template'].sudo().browse(template_id)

        email_values = template.generate_email(order.id, ['body_html', 'subject', 'email_to', 'email_from'])
        email_body = email_values.get('body_html')
        subject = email_values.get('subject')
        email_to = email_values.get('email_to')
        email_from = email_values.get('email_from')

        template.sudo().send_mail(order.id, force_send=True)

        order.message_post(
            body=email_body,
            subject=subject,
            message_type='email',
            subtype_id=self.env.ref('mail.mt_comment').id,
            email_from=email_from,
            email_to=email_to
        )


    def _compute_send_sign(self):
        for o in self:
            if o.sign_id:
                o.send_sign = True
            else:
                o.send_sign = False
            
