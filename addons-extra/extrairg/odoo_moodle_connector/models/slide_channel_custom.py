from odoo import models, fields, api
from . import course_service
from . import constants
from . import utils
import logging


class MoodleSlideChannelPartner(models.Model):
    _inherit = constants.SLIDE_CHANNEL_PARTNER_MODEL

    role = fields.Selection([
        ('1', 'Manager'), ('3', 'Teacher'), ('4', 'Non-Editing-Teacher'), ('5', 'Student')
    ], string='Role', required=True, default='5')


class MoodleSlideChannel(models.Model):
    _inherit = constants.SLIDE_CHANNEL_MODEL

    md_id = fields.Integer(string="Moodle-ID", readonly=True)
    category_id = fields.Many2one(constants.MOODLE_CATEGORIES_MODEL, string="Course Category", required=True)
    short_name = fields.Char(string="Short Name")
    enable_completion = fields.Boolean(default=False, string="Enable Completion?")
    completion_notify = fields.Boolean(default=False, string="Completion Notify?")
    is_visible = fields.Boolean(default=True, string="Visible")
    show_reports = fields.Boolean(default=True, string="Show Reports")

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")
    news_items = fields.Boolean(default=True, string="News Items")
    show_grades = fields.Boolean(default=True, string="Show Grades")
    cs_format = fields.Selection([
        ('weeks', 'Weeks'), ('topics', 'Topics'), ('social', 'Social'), ('site', 'Site')
    ], string="Course Format", default='weeks')
    lang_id = fields.Many2one(constants.RES_LANG_MODEL, string="Language")

    def create(self, values):
        _logging = logging.getLogger(__name__)

        res = super(MoodleSlideChannel, self).create(values)
        credentials = utils.get_moodle_credentials(self_env=self.env)
        if credentials:
            course_obj = course_service.MoodleCourseService(credentials=credentials, self_env=self.env)
            crt_resp = course_obj.create_course(l2s_course=res)
            if crt_resp['err_status']:
                _logging.error("Moodle Course Create Error: " + crt_resp['response'])

        return res

    def write(self, values, addons=None):
        _logging = logging.getLogger(__name__)

        res = super(MoodleSlideChannel, self).write(values)
        if addons is None:
            credentials = utils.get_moodle_credentials(self_env=self.env)
            if credentials:
                course_obj = course_service.MoodleCourseService(credentials=credentials, self_env=self.env)
                for rec in self:
                    crt_resp = course_obj.create_course(l2s_course=rec)
                    if crt_resp['err_status']:
                        _logging.error("Moodle Course Update Error: " + crt_resp['response'])
        return res

    @api.model
    def unlink(self, values=None):
        _logging = logging.getLogger(__name__)

        if values:
            credentials = utils.get_moodle_credentials(self_env=self.env)
            for cors_id in values:
                slide_id = self.env[constants.SLIDE_CHANNEL_MODEL].search([('id', '=', cors_id)])
                if slide_id.md_id and credentials:
                    course_obj = course_service.MoodleCourseService(credentials=credentials, self_env=self.env)
                    del_resp = course_obj.delete_course(l2s_course=slide_id)
                    if del_resp['err_status']:
                        _logging.error("Moodle Course Delete Error: " + del_resp['response'])

                slide_id.unlink()
        return super(MoodleSlideChannel, self).unlink()
