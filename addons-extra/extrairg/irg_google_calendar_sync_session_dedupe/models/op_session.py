from odoo import fields, models


class OpSession(models.Model):
    _inherit = 'op.session'

    google_event_id = fields.Char(string='Google Event ID', index=True, copy=False)
