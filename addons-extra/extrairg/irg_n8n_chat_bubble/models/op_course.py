# -*- coding: utf-8 -*-
from odoo import fields, models


class OpCourse(models.Model):
    _inherit = 'op.course'

    irg_n8n_chat_enabled = fields.Boolean(
        string='Chat n8n Activo',
        default=False,
        help='Habilita una burbuja de chat para este curso en el campus virtual.'
    )
    irg_n8n_chat_webhook_url = fields.Char(
        string='URL Webhook Chat n8n',
        help='URL del webhook de chat de n8n específico para este curso.'
    )
    irg_n8n_chat_title = fields.Char(
        string='Título del Chat',
        default='Soporte Académico',
        help='Título que se mostrará en la cabecera de la burbuja de chat.'
    )
    irg_n8n_chat_welcome_msg = fields.Char(
        string='Mensaje de Bienvenida',
        default='¡Hola! ¿En qué te puedo ayudar hoy?',
        help='Mensaje inicial mostrado al estudiante al abrir el chat.'
    )
