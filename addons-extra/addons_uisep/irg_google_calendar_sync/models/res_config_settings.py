from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    google_calendar_api_key = fields.Char(
        string='Google API Key',
        config_parameter='irg_google_calendar_sync.api_key',
        help='API Key from Google Cloud Console'
    )
    google_calendar_id = fields.Char(
        string='Google Calendar ID',
        config_parameter='irg_google_calendar_sync.calendar_id',
        help='ID of the Google Calendar to sync (e.g., xxx@group.calendar.google.com)'
    )
    google_calendar_sync_enabled = fields.Boolean(
        string='Enable Auto Sync',
        config_parameter='irg_google_calendar_sync.enabled',
        default=False,
        help='Enable automatic synchronization from Google Calendar'
    )
    google_calendar_sync_days = fields.Integer(
        string='Sync Days Ahead',
        config_parameter='irg_google_calendar_sync.sync_days',
        default=30,
        help='Number of days ahead to sync events'
    )
