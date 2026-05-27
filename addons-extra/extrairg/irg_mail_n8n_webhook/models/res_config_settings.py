# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    irg_mail_n8n_enabled = fields.Boolean(
        string='Enviar correos por n8n',
        config_parameter='irg_mail_n8n_webhook.enabled',
    )
    irg_mail_n8n_webhook_url = fields.Char(
        string='URL webhook n8n',
        config_parameter='irg_mail_n8n_webhook.webhook_url',
    )
    irg_mail_n8n_auth_token = fields.Char(
        string='Token Bearer n8n',
        config_parameter='irg_mail_n8n_webhook.auth_token',
    )
    irg_mail_n8n_timeout = fields.Integer(
        string='Timeout n8n',
        config_parameter='irg_mail_n8n_webhook.timeout',
        default=15,
    )
    irg_mail_n8n_max_attempts = fields.Integer(
        string='Intentos maximos',
        config_parameter='irg_mail_n8n_webhook.max_attempts',
        default=5,
    )
    irg_mail_n8n_max_attachment_mb = fields.Integer(
        string='Limite adjunto MB',
        config_parameter='irg_mail_n8n_webhook.max_attachment_mb',
        default=10,
    )
    irg_mail_n8n_debug_payload = fields.Boolean(
        string='Registrar payload en logs',
        config_parameter='irg_mail_n8n_webhook.debug_payload',
    )