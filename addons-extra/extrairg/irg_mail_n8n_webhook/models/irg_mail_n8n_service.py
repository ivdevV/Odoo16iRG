# -*- coding: utf-8 -*-

import base64
import hashlib
import json
import logging
from urllib import error, request

from odoo import _, api, fields, models


_logger = logging.getLogger(__name__)


class IrgMailN8nService(models.AbstractModel):
    _name = 'irg.mail.n8n.service'
    _description = 'Servicio de envio de correo por webhook n8n'

    @api.model
    def _is_enabled(self):
        return self._get_bool_param('irg_mail_n8n_webhook.enabled', False)

    @api.model
    def _get_bool_param(self, key, default=False):
        value = self.env['ir.config_parameter'].sudo().get_param(
            key,
            'True' if default else 'False',
        )
        return str(value).lower() in ('1', 'true', 'yes', 'y')

    @api.model
    def _get_int_param(self, key, default=0, minimum=None, maximum=None):
        raw_value = self.env['ir.config_parameter'].sudo().get_param(key, str(default))
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            value = default
        if minimum is not None:
            value = max(minimum, value)
        if maximum is not None:
            value = min(maximum, value)
        return value

    @api.model
    def _get_config(self):
        params = self.env['ir.config_parameter'].sudo()
        return {
            'enabled': self._is_enabled(),
            'webhook_url': params.get_param('irg_mail_n8n_webhook.webhook_url', '').strip(),
            'auth_token': params.get_param('irg_mail_n8n_webhook.auth_token', '').strip(),
            'timeout': self._get_int_param('irg_mail_n8n_webhook.timeout', 15, minimum=1, maximum=120),
            'max_attachment_mb': self._get_int_param(
                'irg_mail_n8n_webhook.max_attachment_mb',
                10,
                minimum=1,
                maximum=100,
            ),
            'debug_payload': self._get_bool_param('irg_mail_n8n_webhook.debug_payload', False),
        }

    @api.model
    def _idempotency_key(self, mail):
        return 'odoo-mail-%s-%s' % (self.env.cr.dbname, mail.id)

    @api.model
    def _get_or_create_delivery(self, mail):
        key = self._idempotency_key(mail)
        delivery_model = self.env['irg.mail.n8n.delivery'].sudo()
        delivery = delivery_model.search([('idempotency_key', '=', key)], limit=1)
        if delivery:
            return delivery
        return delivery_model.create({
            'mail_id': mail.id,
            'idempotency_key': key,
            'state': 'pending',
        })

    @api.model
    def _dispatch_mail(self, mail):
        delivery = self._get_or_create_delivery(mail)
        if delivery.state == 'sent':
            mail.write({'state': 'sent', 'failure_reason': False})
            return True
        return self._send_delivery(delivery)

    @api.model
    def _send_delivery(self, delivery):
        delivery.ensure_one()
        mail = delivery.mail_id
        if not mail:
            delivery.write({
                'state': 'cancelled',
                'failure_reason': _('El correo Odoo asociado ya no existe.'),
                'next_attempt_at': False,
            })
            return False

        config = self._get_config()
        if not config['enabled']:
            return False
        if not config['webhook_url'] or not config['auth_token']:
            message = _('La URL o el token del webhook n8n no estan configurados.')
            delivery.write({'attempt_count': delivery.attempt_count + 1})
            delivery._schedule_retry(message)
            return False

        try:
            payload = self._build_payload(mail, delivery, config)
        except ValueError as exc:
            message = str(exc)
            delivery.write({'attempt_count': delivery.attempt_count + 1})
            delivery._schedule_retry(message)
            return False

        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        payload_hash = hashlib.sha256(payload_json.encode('utf-8')).hexdigest()
        delivery.write({
            'attempt_count': delivery.attempt_count + 1,
            'last_attempt_at': fields.Datetime.now(),
            'webhook_url': config['webhook_url'],
            'payload_hash': payload_hash,
        })

        try:
            status, body = self._post_json(
                config['webhook_url'],
                payload_json,
                config['auth_token'],
                delivery.idempotency_key,
                config['timeout'],
            )
        except Exception as exc:
            _logger.warning('n8n mail webhook request failed for mail %s: %s', mail.id, exc)
            delivery._schedule_retry(_('No se pudo contactar con n8n: %s') % exc)
            return False

        if 200 <= status < 300:
            delivery._mark_sent(response_status=status, response_body=body)
            return True

        message = _('n8n respondio con estado HTTP %s.') % status
        delivery._schedule_retry(message, response_status=status, response_body=body)
        return False

    @api.model
    def _build_payload(self, mail, delivery, config=None):
        config = config or self._get_config()
        max_bytes = config['max_attachment_mb'] * 1024 * 1024
        attachments = self._build_attachments(mail, max_bytes)
        recipients = self._build_recipients(mail)
        message = mail.mail_message_id
        author = message.author_id if message else False
        company = getattr(mail, 'company_id', False) or self.env.company
        payload = {
            'idempotency_key': delivery.idempotency_key,
            'odoo': {
                'database': self.env.cr.dbname,
                'base_url': self.env['ir.config_parameter'].sudo().get_param('web.base.url', ''),
                'company_id': company.id if company else False,
                'company_name': company.name if company else False,
            },
            'mail': {
                'id': mail.id,
                'message_id': getattr(mail, 'message_id', False) or False,
                'mail_message_id': message.id if message else False,
                'model': getattr(mail, 'model', False) or (message.model if message else False),
                'res_id': getattr(mail, 'res_id', False) or (message.res_id if message else False),
                'subject': mail.subject or '',
                'body_html': mail.body_html or '',
                'email_from': mail.email_from or '',
                'reply_to': getattr(mail, 'reply_to', False) or '',
                'email_to': mail.email_to or '',
                'email_cc': getattr(mail, 'email_cc', False) or '',
                'auto_delete': bool(getattr(mail, 'auto_delete', False)),
            },
            'recipients': recipients,
            'author': {
                'id': author.id if author else False,
                'name': author.name if author else False,
                'email': author.email if author else False,
            },
            'attachments': attachments,
            'created_at': fields.Datetime.to_string(mail.create_date) if mail.create_date else False,
        }
        if config.get('debug_payload'):
            _logger.info('n8n mail payload for mail %s: %s', mail.id, payload)
        return payload

    @api.model
    def _build_recipients(self, mail):
        recipients = []
        for partner in getattr(mail, 'recipient_ids', self.env['res.partner']):
            recipients.append({
                'partner_id': partner.id,
                'name': partner.name,
                'email': partner.email,
                'type': 'to',
            })
        if getattr(mail, 'email_to', False):
            recipients.append({
                'partner_id': False,
                'name': False,
                'email': mail.email_to,
                'type': 'to_raw',
            })
        email_cc = getattr(mail, 'email_cc', False)
        if email_cc:
            recipients.append({
                'partner_id': False,
                'name': False,
                'email': email_cc,
                'type': 'cc_raw',
            })
        return recipients

    @api.model
    def _build_attachments(self, mail, max_bytes):
        attachments = []
        for attachment in getattr(mail, 'attachment_ids', self.env['ir.attachment']):
            content = base64.b64decode(attachment.datas or b'')
            if len(content) > max_bytes:
                raise ValueError(
                    _('El adjunto %s supera el limite configurado para n8n.') % attachment.name
                )
            attachments.append({
                'id': attachment.id,
                'name': attachment.name,
                'mimetype': attachment.mimetype,
                'size': len(content),
                'content_base64': base64.b64encode(content).decode('ascii'),
            })
        return attachments

    @api.model
    def _post_json(self, webhook_url, payload_json, auth_token, idempotency_key, timeout):
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': 'Bearer %s' % auth_token,
            'Idempotency-Key': idempotency_key,
        }
        req = request.Request(
            webhook_url,
            data=payload_json.encode('utf-8'),
            headers=headers,
            method='POST',
        )
        try:
            with request.urlopen(req, timeout=timeout) as response:
                body = response.read().decode('utf-8', errors='replace')[:2000]
                return response.getcode(), body
        except error.HTTPError as exc:
            body = exc.read().decode('utf-8', errors='replace')[:2000]
            return exc.code, body