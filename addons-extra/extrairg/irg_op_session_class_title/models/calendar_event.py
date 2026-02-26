from odoo import models


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    def write(self, vals):
        res = super().write(vals)
        if 'name' not in vals:
            return res

        Session = self.env['op.session'].sudo()
        for event in self.filtered(lambda rec: rec.google_event_id):
            sessions = Session.search([('google_event_id', '=', event.google_event_id)])
            if sessions:
                sessions.write({'class_title': event.name})
        return res
