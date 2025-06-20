from odoo import models, fields, api
from . import calendar_service
from . import constants
from . import utils
import logging


class MoodleCalendarEvent(models.Model):
    _inherit = constants.CALENDAR_EVENT_MODEL

    md_id = fields.Integer(string="Moodle-ID", readonly=True)
    slide_id = fields.Many2one(constants.SLIDE_CHANNEL_MODEL, string='Course')
    is_visible = fields.Boolean(string="Visible", default=True)

    @api.model
    def create(self, values):
        _logging = logging.getLogger(__name__)

        res = super(MoodleCalendarEvent, self).create(values)
        credentials = utils.get_moodle_credentials(self_env=self.env)
        if credentials:
            calendar_event_obj = calendar_service.MoodleCalendarService(credentials=credentials, self_env=self.env)
            crt_resp = calendar_event_obj.create_event(l2s_event=res)
            if crt_resp['err_status']:
                _logging.error("Moodle Calendar Event Create/Update Error: " + crt_resp['response'])

        return res

    def write(self, values, addons=None):
        _logging = logging.getLogger(__name__)

        res = super(MoodleCalendarEvent, self).write(values)
        # if addons is None:
        #     credentials = utils.get_moodle_credentials(self_env=self.env)
        #     if credentials:
        #         calendar_event_obj = calendar_service.MoodleCalendarService(credentials=credentials, self_env=self.env)
        #         for rec in self:
        #             crt_resp = calendar_event_obj.create_event(l2s_event=rec)
        #             if crt_resp['err_status']:
        #                 _logging.error("Moodle Calendar Event Create/Update Error: " + crt_resp['response'])
        return res

    @api.model
    def unlink(self, values=None):
        _logging = logging.getLogger(__name__)

        if values:
            credentials = utils.get_moodle_credentials(self_env=self.env)
            for event_id in values:
                calendar_event_id = self.env[constants.CALENDAR_EVENT_MODEL].search([('id', '=', event_id)])
                if calendar_event_id.md_id and credentials:
                    calendar_event_obj = calendar_service.MoodleCalendarService(
                        credentials=credentials, self_env=self.env)
                    del_resp = calendar_event_obj.delete_event(l2s_event=calendar_event_id)
                    if del_resp['err_status']:
                        _logging.error("Moodle Calendar Event Delete Error: " + del_resp['response'])

                calendar_event_id.unlink()
        return super(MoodleCalendarEvent, self).unlink()
