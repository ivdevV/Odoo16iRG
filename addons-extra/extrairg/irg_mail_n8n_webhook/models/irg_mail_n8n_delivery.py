# -*- coding: utf-8 -*-

from datetime import timedelta

from odoo import _, api, fields, models


class IrgMailN8nDelivery(models.Model):
    _name = 'irg.mail.n8n.delivery'
    _description = 'Entrega de correo mediante webhook n8n'
    _order = 'create_date desc, id desc'
    _rec_name = 'idempotency_key'

    mail_id = fields.Many2one(
        'mail.mail',
        string='Correo Odoo',
        index=True,
        ondelete='set null',
    )
    state = fields.Selection([
        ('pending', 'Pendiente'),
        ('sent', 'Enviado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
    ], string='Estado', default='pending', required=True, index=True)
    attempt_count = fields.Integer(string='Intentos', default=0, required=True)
    next_attempt_at = fields.Datetime(string='Proximo intento', index=True)
    last_attempt_at = fields.Datetime(string='Ultimo intento')
    sent_at = fields.Datetime(string='Enviado en')
    idempotency_key = fields.Char(string='Clave de idempotencia', required=True, index=True)
    webhook_url = fields.Char(string='URL webhook')
    response_status = fields.Integer(string='Estado HTTP')
    response_body = fields.Text(string='Respuesta')
    failure_reason = fields.Text(string='Motivo de fallo')
    payload_hash = fields.Char(string='Hash payload', index=True)

    _sql_constraints = [
        (
            'idempotency_key_unique',
            'unique(idempotency_key)',
            'La clave de idempotencia de n8n debe ser unica.',
        ),
    ]

    @api.model
    def _retry_delay_minutes(self, attempt_count):
        return min(60, max(1, 2 ** max(attempt_count - 1, 0)))

    def _schedule_retry(self, message, response_status=False, response_body=False):
        self.ensure_one()
        max_attempts = self.env['irg.mail.n8n.service']._get_int_param(
            'irg_mail_n8n_webhook.max_attempts',
            5,
            minimum=1,
        )
        values = {
            'last_attempt_at': fields.Datetime.now(),
            'response_status': response_status or False,
            'response_body': response_body or False,
            'failure_reason': message,
        }
        if self.attempt_count >= max_attempts:
            values.update({
                'state': 'failed',
                'next_attempt_at': False,
            })
            self.mail_id.write({
                'state': 'exception',
                'failure_reason': message,
            })
            self.mail_id._postprocess_sent_message(
                success_pids=[],
                failure_type='mail_smtp',
            )
        else:
            values.update({
                'state': 'failed',
                'next_attempt_at': fields.Datetime.now() + timedelta(
                    minutes=self._retry_delay_minutes(self.attempt_count)
                ),
            })
            if self.mail_id.state == 'exception':
                self.mail_id.write({'state': 'outgoing'})
        self.write(values)

    def _mark_sent(self, response_status=False, response_body=False):
        self.ensure_one()
        now = fields.Datetime.now()
        self.write({
            'state': 'sent',
            'last_attempt_at': now,
            'sent_at': now,
            'next_attempt_at': False,
            'response_status': response_status or False,
            'response_body': response_body or False,
            'failure_reason': False,
        })
        self.mail_id.write({
            'state': 'sent',
            'failure_reason': False,
        })
        self.mail_id._postprocess_sent_message(
            success_pids=getattr(self.mail_id, 'recipient_ids', self.env['res.partner']).ids,
            failure_type=False,
        )

    @api.model
    def _cron_retry_pending_deliveries(self, limit=50):
        service = self.env['irg.mail.n8n.service']
        if not service._is_enabled():
            return True

        now = fields.Datetime.now()
        # Technical retry queue must process records regardless of the original sender.
        deliveries = self.sudo().search([
            ('state', 'in', ['pending', 'failed']),
            '|',
            ('next_attempt_at', '=', False),
            ('next_attempt_at', '<=', now),
        ], limit=limit, order='next_attempt_at asc, id asc')
        for delivery in deliveries:
            if delivery.mail_id and delivery.mail_id.state != 'sent':
                service._send_delivery(delivery)
        return True

    def action_retry_now(self):
        service = self.env['irg.mail.n8n.service']
        for delivery in self:
            delivery.write({
                'state': 'pending',
                'next_attempt_at': False,
                'failure_reason': False,
            })
            service._send_delivery(delivery)
        return True

    def action_cancel(self):
        self.write({'state': 'cancelled', 'next_attempt_at': False})
        return True