# -*- coding: utf-8 -*-
from odoo import models, fields, api


class StripeEventLog(models.Model):
    _name = 'stripe.event.log'
    _description = 'Stripe Event Log'
    _order = 'received_at desc, id desc'

    event_id = fields.Char(string='ID Evento Stripe', required=True, index=True)
    event_type = fields.Char(string='Tipo de Evento', index=True)
    received_at = fields.Datetime(string='Recibido el', default=fields.Datetime.now, required=True)
    processed = fields.Boolean(string='Procesado', default=False, index=True)
    error = fields.Text(string='Mensaje de Error')
    payload = fields.Text(string='Payload JSON')

    _sql_constraints = [
        ('event_id_unique', 'unique(event_id)', 'El ID del evento de Stripe debe ser único.'),
    ]
