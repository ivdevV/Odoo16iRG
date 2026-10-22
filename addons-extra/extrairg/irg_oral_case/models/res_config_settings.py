# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    irg_oral_case_n8n_submit_url = fields.Char(
        string='URL de entrega n8n',
        config_parameter='irg_oral_case.n8n_submit_url',
    )
    irg_oral_case_n8n_status_url = fields.Char(
        string='URL de estado n8n',
        config_parameter='irg_oral_case.n8n_status_url',
    )
    irg_oral_case_api_key = fields.Char(
        string='Clave X-IRG-Key',
        config_parameter='irg_oral_case.api_key',
    )
    irg_oral_case_max_video_bytes = fields.Integer(
        string='Tamaño máximo del vídeo (bytes)',
        config_parameter='irg_oral_case.max_video_bytes',
        default=52428800,
    )
    irg_oral_case_max_duration_seconds = fields.Integer(
        string='Duración máxima (segundos)',
        config_parameter='irg_oral_case.max_duration_seconds',
        default=600,
    )
    irg_oral_case_retention_days = fields.Integer(
        string='Días de retención del vídeo',
        config_parameter='irg_oral_case.retention_days',
        default=0,
    )
    irg_oral_case_retention_enabled = fields.Boolean(
        string='Activar borrado de vídeos',
        config_parameter='irg_oral_case.retention_enabled',
        default=False,
    )
    irg_oral_case_store_video_copy = fields.Boolean(
        string='Guardar copia del vídeo en Odoo',
        config_parameter='irg_oral_case.store_video_copy',
        default=False,
    )
