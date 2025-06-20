from odoo import models, fields
from datetime import timedelta
from . import category_service
from . import calendar_service
from . import course_service
from . import user_service
from . import constants
from . import utils
import logging


class MoodleConnector(models.Model):
    _name = constants.MOODLE_CONNECTOR_MODEL
    _description = constants.MOODLE_CONNECTOR_MODEL_DESC

    connector = fields.One2many(constants.MOODLE_CONNECTOR_MODEL, inverse_name='connector', string="Reference")
    custom_from_datetime = fields.Datetime(
        string='From Date', default=lambda self: (fields.datetime.now() - timedelta(hours=1)))
    custom_to_datetime = fields.Datetime(
        string='To Date', default=lambda self: (fields.datetime.now() + timedelta(hours=1)))

    import_user = fields.Boolean(default=False, string="User")
    import_category = fields.Boolean(default=False, string="Category")
    import_course = fields.Boolean(default=False, string="Course")
    import_event = fields.Boolean(default=False, string="Event")

    export_user = fields.Boolean(default=False, string="User")
    export_category = fields.Boolean(default=False, string="Category")
    export_course = fields.Boolean(default=False, string="Course")
    export_event = fields.Boolean(default=False, string="Event")

    def synchronize(self):
        _logging = logging.getLogger(__name__)

        pop_up_message, date_error_chk = "", False
        import_chk_status, export_chk_status = False, False
        new_imp_category, new_imp_course, new_imp_user, new_imp_event = 0, 0, 0, 0
        upd_imp_category, upd_imp_course, upd_imp_user, upd_imp_event = 0, 0, 0, 0
        new_exp_category, new_exp_course, new_exp_user, new_exp_event = 0, 0, 0, 0
        upd_exp_category, upd_exp_course, upd_exp_user = 0, 0, 0

        try:
            # if self.custom_from_datetime > self.custom_to_datetime:
            #     date_error_chk = True

            if not date_error_chk:
                md_credentials = utils.get_moodle_credentials(self_env=self.env)
                if md_credentials:

                    if self.import_category or self.export_category:
                        _category = category_service.MoodleCategoryService(
                            credentials=md_credentials, self_env=self.env)
                            # initial_date=self.custom_from_datetime, end_date=self.custom_to_datetime)

                        if self.import_category:
                            category_response = _category.import_categories()
                            if not category_response["err_status"]:
                                new_imp_category += category_response["success"]
                                upd_imp_category += category_response["updated"]
                        if self.export_category:
                            category_response = _category.export_categories()
                            if not category_response["err_status"]:
                                new_exp_category += category_response["success"]
                                upd_exp_category += category_response["updated"]

                    if self.import_course or self.export_course:
                        _course = course_service.MoodleCourseService(credentials=md_credentials, self_env=self.env)
                            # initial_date=self.custom_from_datetime, end_date=self.custom_to_datetime)

                        if self.import_course:
                            course_response = _course.import_courses()
                            if not course_response["err_status"]:
                                new_imp_course += course_response["success"]
                                upd_imp_course += course_response["updated"]
                        if self.export_course:
                            course_response = _course.export_courses()
                            if not course_response["err_status"]:
                                new_exp_course += course_response["success"]
                                upd_exp_course += course_response["updated"]

                    if self.import_user or self.export_user:
                        _user = user_service.MoodleUserService(credentials=md_credentials, self_env=self.env)
                            # initial_date=self.custom_from_datetime, end_date=self.custom_to_datetime)

                        if self.import_user:
                            user_response = _user.import_users()
                            if not user_response["err_status"]:
                                new_imp_user += user_response["success"]
                                upd_imp_user += user_response["updated"]
                        if self.export_user:
                            user_response = _user.export_users()
                            if not user_response["err_status"]:
                                new_exp_user += user_response["success"]
                                upd_exp_user += user_response["updated"]

                    if self.import_event or self.export_event:
                        _event = calendar_service.MoodleCalendarService(credentials=md_credentials, self_env=self.env)
                            # initial_date=self.custom_from_datetime, end_date=self.custom_to_datetime)

                        if self.import_event:
                            event_response = _event.import_events()
                            if not event_response["err_status"]:
                                new_imp_event += event_response["success"]
                                upd_imp_event += event_response["updated"]
                        if self.export_course:
                            event_response = _event.export_events()
                            if not event_response["err_status"]:
                                new_exp_event += event_response["success"]

                    if self.import_category or self.import_course or self.import_user or self.import_event:
                        if new_imp_category or upd_imp_category or new_imp_course or upd_imp_course or \
                                new_imp_user or upd_imp_user or new_imp_event or upd_imp_event:
                            self.env[constants.MOODLE_IMPORT_STATS_MODEL].create({
                                'new_category': new_imp_category, 'upd_category': upd_imp_category,
                                'new_course': new_imp_course, 'upd_course': upd_imp_course,
                                'new_user': new_imp_user, 'upd_user': upd_imp_user,
                                'new_event': new_imp_event, 'upd_event': upd_imp_event,
                                'connector': self.id
                            })
                        if pop_up_message == "":
                            pop_up_message += constants.MDL_SYNC_PROCESS_MSG
                        import_chk_status = True

                    if self.export_category or self.export_course or self.export_user or self.export_event:
                        if new_exp_category or upd_exp_category or new_exp_course or upd_exp_course or \
                                new_exp_user or upd_exp_user or new_exp_event:
                            self.env[constants.MOODLE_EXPORT_STATS_MODEL].create({
                                'new_category': new_exp_category, 'upd_category': upd_exp_category,
                                'new_course': new_exp_course, 'upd_course': upd_exp_course,
                                'new_user': new_exp_user, 'upd_user': upd_exp_user,
                                'new_event': new_exp_event, 'connector': self.id
                            })
                        if pop_up_message == "":
                            pop_up_message += constants.MDL_SYNC_PROCESS_MSG
                        export_chk_status = True

                    if not export_chk_status and not import_chk_status:
                        pop_up_message = constants.MDL_NO_OPT_SECTION_ERR

                else:
                    pop_up_message += constants.MDL_CREDENTIALS_NOT_FND
                    _logging.info("Sage Connector Error while Fetching Credentials Sync: ")
            # else:
            #     pop_up_message += constants.INVALID_DATE_RANGES
        except Exception as ex:
            _logging.exception("Moodle Connector Synchronization Exception: " + str(ex))
            pop_up_message += constants.MDL_CONNECTOR_SYNC_EXCEPT
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "System Notification",
                'message': pop_up_message,
                'sticky': False,
            }
        }

    def import_history_action(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': constants.MOODLE_IMPORT_STATS_MODEL,
            'view_mode': 'tree',
            'context': {'no_breadcrumbs': True}
        }

    def export_history_action(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': constants.MOODLE_EXPORT_STATS_MODEL,
            'view_mode': 'tree',
            'context': {'no_breadcrumbs': True}
        }
