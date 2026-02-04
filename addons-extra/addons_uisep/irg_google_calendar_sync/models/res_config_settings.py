from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

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

    def action_sync_google_calendar_now(self):
        """Manual trigger to sync Google Calendar immediately"""
        _logger.info("Manual Google Calendar sync triggered from settings")
        
        # Log current config for debugging
        ICP = self.env['ir.config_parameter'].sudo()
        api_key = ICP.get_param('irg_google_calendar_sync.api_key', '')
        calendar_id = ICP.get_param('irg_google_calendar_sync.calendar_id', '')
        enabled = ICP.get_param('irg_google_calendar_sync.enabled', '')
        sync_days = int(ICP.get_param('irg_google_calendar_sync.sync_days', '30'))
        
        _logger.info(f"Config - API Key: {'SET' if api_key else 'NOT SET'}, Calendar ID: {calendar_id}, Enabled: {enabled}, Days: {sync_days}")
        
        # Force sync regardless of enabled flag
        CalendarEvent = self.env['calendar.event']
        if api_key and calendar_id:
            CalendarEvent._fetch_and_sync_google_events(api_key, calendar_id, sync_days)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Sincronización completada',
                    'message': f'Sincronizados eventos de los próximos {sync_days} días. Revisa los logs.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error de configuración',
                    'message': 'Falta API Key o Calendar ID. Guarda la configuración primero.',
                    'type': 'danger',
                    'sticky': True,
                }
            }
