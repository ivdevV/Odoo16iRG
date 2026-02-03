from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Add settings here if needed later
    # google_calendar_sync_create_missing = fields.Boolean(...)
