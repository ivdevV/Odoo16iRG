import pytz

from odoo import api, fields, models


class OpSession(models.Model):
    _inherit = 'op.session'

    class_title = fields.Char(string='Class Title', index=True)

    @api.depends('class_title', 'faculty_id', 'subject_id', 'start_datetime', 'end_datetime')
    def _compute_name(self):
        user_tz = self.env.user.tz if isinstance(self.env.user.tz, str) else 'UTC'
        try:
            tz = pytz.timezone(user_tz)
        except pytz.UnknownTimeZoneError:
            tz = pytz.timezone('UTC')

        for session in self:
            if session.class_title:
                session.name = session.class_title
            elif session.subject_id:
                session.name = session.subject_id.name
            elif session.faculty_id and session.start_datetime and session.end_datetime:
                session.name = (
                    f"{session.faculty_id.name}:"
                    f"{session.start_datetime.astimezone(tz).strftime('%I:%M%p')}"
                    f"-{session.end_datetime.astimezone(tz).strftime('%I:%M%p')}"
                )
            else:
                session.name = False

    @api.model_create_multi
    def create(self, vals_list):
        CalendarEvent = self.env['calendar.event'].sudo()
        for vals in vals_list:
            if not vals.get('class_title') and vals.get('google_event_id'):
                event = CalendarEvent.search([('google_event_id', '=', vals['google_event_id'])], limit=1)
                if event and event.name:
                    vals['class_title'] = event.name
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if 'google_event_id' in vals and 'class_title' not in vals:
            CalendarEvent = self.env['calendar.event'].sudo()
            for session in self.filtered(lambda rec: rec.google_event_id and not rec.class_title):
                event = CalendarEvent.search([('google_event_id', '=', session.google_event_id)], limit=1)
                if event and event.name:
                    super(OpSession, session).write({'class_title': event.name})
        return res
