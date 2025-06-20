from odoo import models, fields, api
from . import category_service
from . import calendar_service
from . import course_service
from . import user_service
from . import constants
from . import utils
import logging


class MoodleCronJobSettings(models.Model):
    _name = constants.MOODLE_CRONJOB_SETTINGS_MODEL
    _description = constants.MOODLE_CRONJOB_SETTINGS_MODEL_DESC

    ###############################################################################################################
    # #######################################       For User Options     #######################################
    ###############################################################################################################

    is_auto_import_user = fields.Boolean(default=lambda self: self.get_auto_import_status_user())
    import_interval_num_user = fields.Integer(default=lambda self: self.get_import_interval_num_user())
    import_call_num_user = fields.Selection(
        [('1', 'One Time'), ('-1', 'Unlimited Time')], default=lambda self: self.get_import_call_num_user())
    import_interval_type_user = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
        default=lambda self: self.get_import_interval_type_user())

    is_auto_export_user = fields.Boolean(default=lambda self: self.get_auto_export_status_user())
    export_interval_num_user = fields.Integer(default=lambda self: self.get_export_interval_num_user())
    export_call_num_user = fields.Selection(
        [('1', 'One Time'), ('-1', 'Unlimited Time')], default=lambda self: self.get_export_call_num_user())
    export_interval_type_user = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
        default=lambda self: self.get_export_interval_type_user())

    ##############################################################################################################
    # #######################################      For Category Options     #######################################
    ##############################################################################################################

    is_auto_import_category = fields.Boolean(default=lambda self: self.get_auto_import_status_category())
    import_interval_num_category = fields.Integer(default=lambda self: self.get_import_interval_num_category())
    import_call_num_category = fields.Selection(
        [('1', 'One Time'), ('-1', 'Unlimited Time')], default=lambda self: self.get_import_call_num_category())
    import_interval_type_category = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
        default=lambda self: self.get_import_interval_type_category())

    is_auto_export_category = fields.Boolean(default=lambda self: self.get_auto_export_status_category())
    export_interval_num_category = fields.Integer(default=lambda self: self.get_export_interval_num_category())
    export_call_num_category = fields.Selection(
        [('1', 'One Time'), ('-1', 'Unlimited Time')], default=lambda self: self.get_export_call_num_category())
    export_interval_type_category = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
        default=lambda self: self.get_export_interval_type_category())

    ##############################################################################################################
    # #######################################      For Course Options     #######################################
    ##############################################################################################################

    is_auto_import_course = fields.Boolean(default=lambda self: self.get_auto_import_status_course())
    import_interval_num_course = fields.Integer(default=lambda self: self.get_import_interval_num_course())
    import_call_num_course = fields.Selection(
        [('1', 'One Time'), ('-1', 'Unlimited Time')], default=lambda self: self.get_import_call_num_course())
    import_interval_type_course = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
        default=lambda self: self.get_import_interval_type_course())

    is_auto_export_course = fields.Boolean(default=lambda self: self.get_auto_export_status_course())
    export_interval_num_course = fields.Integer(default=lambda self: self.get_export_interval_num_course())
    export_call_num_course = fields.Selection(
        [('1', 'One Time'), ('-1', 'Unlimited Time')], default=lambda self: self.get_export_call_num_course())
    export_interval_type_course = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
        default=lambda self: self.get_export_interval_type_course())

    ###############################################################################################################
    # ######################################          For Event Options         ####################################
    ###############################################################################################################

    is_auto_import_event = fields.Boolean(default=lambda self: self.get_auto_import_status_event())
    import_interval_num_event = fields.Integer(default=lambda self: self.get_import_interval_num_event())
    import_call_num_event = fields.Selection(
        [('1', 'One Time'), ('-1', 'Unlimited Time')], default=lambda self: self.get_import_call_num_event())
    import_interval_type_event = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
        default=lambda self: self.get_import_interval_type_event())

    is_auto_export_event = fields.Boolean(default=lambda self: self.get_auto_export_status_event())
    export_interval_num_event = fields.Integer(default=lambda self: self.get_export_interval_num_event())
    export_call_num_event = fields.Selection(
        [('1', 'One Time'), ('-1', 'Unlimited Time')], default=lambda self: self.get_export_call_num_event())
    export_interval_type_event = fields.Selection(
        [('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
        default=lambda self: self.get_export_interval_type_event())

    ##############################################################################################################
    # ################################      For Default Function Operations     ##################################
    ##############################################################################################################

    def import_users(self):
        _logging = logging.getLogger(__name__)

        credentials = utils.get_moodle_credentials(self_env=self.env)
        if credentials:
            _users = user_service.MoodleUserService(credentials=credentials, self_env=self.env)
            user_response = _users.import_users()
            if not user_response["err_status"]:
                new_imp_user = user_response["success"]
                upd_imp_user = user_response["updated"]
                if new_imp_user or upd_imp_user:
                    self.env[constants.MOODLE_IMPORT_STATS_MODEL].create({
                        'new_user': new_imp_user, 'upd_user': upd_imp_user
                    })
            else:
                _logging.error("Moodle User Import Error: " + user_response["response"])
        else:
            _logging.error(constants.MDL_CREDENTIALS_NOT_FND)

    def export_users(self):
        _logging = logging.getLogger(__name__)

        credentials = utils.get_moodle_credentials(self_env=self.env)
        if credentials:
            _users = user_service.MoodleUserService(credentials=credentials, self_env=self.env)
            user_response = _users.export_users()
            if not user_response["err_status"]:
                new_exp_user = user_response["success"]
                upd_exp_user = user_response["updated"]
                if new_exp_user or upd_exp_user:
                    self.env[constants.MOODLE_EXPORT_STATS_MODEL].create({
                        'new_user': new_exp_user, 'upd_user': upd_exp_user
                    })
            else:
                _logging.error("Moodle User Export Error: " + user_response["response"])
        else:
            _logging.error(constants.MDL_CREDENTIALS_NOT_FND)

    def import_categories(self):
        _logging = logging.getLogger(__name__)

        credentials = utils.get_moodle_credentials(self_env=self.env)
        if credentials:
            _categories = category_service.MoodleCategoryService(credentials=credentials, self_env=self.env)
            category_response = _categories.import_categories()
            if not category_response["err_status"]:
                new_imp_category = category_response["success"]
                upd_imp_category = category_response["updated"]
                if new_imp_category or upd_imp_category:
                    self.env[constants.MOODLE_IMPORT_STATS_MODEL].create({
                        'new_category': new_imp_category, 'upd_category': upd_imp_category
                    })
            else:
                _logging.error("Moodle Category Import Error: " + category_response["response"])
        else:
            _logging.error(constants.MDL_CREDENTIALS_NOT_FND)

    def export_categories(self):
        _logging = logging.getLogger(__name__)

        credentials = utils.get_moodle_credentials(self_env=self.env)
        if credentials:
            _categories = category_service.MoodleCategoryService(credentials=credentials, self_env=self.env)
            category_response = _categories.export_categories()
            if not category_response["err_status"]:
                new_exp_category = category_response["success"]
                upd_exp_category = category_response["updated"]
                if new_exp_category or upd_exp_category:
                    self.env[constants.MOODLE_EXPORT_STATS_MODEL].create({
                        'new_category': new_exp_category, 'upd_category': upd_exp_category
                    })
            else:
                _logging.error("Moodle Category Export Error: " + category_response["response"])
        else:
            _logging.error(constants.MDL_CREDENTIALS_NOT_FND)

    def import_courses(self):
        _logging = logging.getLogger(__name__)

        credentials = utils.get_moodle_credentials(self_env=self.env)
        if credentials:
            _course = course_service.MoodleCourseService(credentials=credentials, self_env=self.env)
            course_response = _course.import_courses()
            if not course_response["err_status"]:
                new_imp_course = course_response["success"]
                upd_imp_course = course_response["updated"]
                if new_imp_course or upd_imp_course:
                    self.env[constants.MOODLE_IMPORT_STATS_MODEL].create({
                        'new_course': new_imp_course, 'upd_course': upd_imp_course
                    })
            else:
                _logging.error("Moodle Courses Import Error: " + course_response["response"])
        else:
            _logging.error(constants.MDL_CREDENTIALS_NOT_FND)

    def export_courses(self):
        _logging = logging.getLogger(__name__)

        credentials = utils.get_moodle_credentials(self_env=self.env)
        if credentials:
            _course = course_service.MoodleCourseService(credentials=credentials, self_env=self.env)
            course_response = _course.export_courses()
            if not course_response["err_status"]:
                new_exp_course = course_response["success"]
                upd_exp_course = course_response["updated"]
                if new_exp_course or upd_exp_course:
                    self.env[constants.MOODLE_EXPORT_STATS_MODEL].create({
                        'new_course': new_exp_course, 'upd_course': upd_exp_course
                    })
            else:
                _logging.error("Moodle Courses Import Error: " + course_response["response"])
        else:
            _logging.error(constants.MDL_CREDENTIALS_NOT_FND)

    def import_events(self):
        _logging = logging.getLogger(__name__)

        credentials = utils.get_moodle_credentials(self_env=self.env)
        if credentials:
            _event = calendar_service.MoodleCalendarService(credentials=credentials, self_env=self.env)
            event_response = _event.import_events()
            if not event_response["err_status"]:
                new_imp_event = event_response["success"]
                upd_imp_event = event_response["updated"]
                if new_imp_event or upd_imp_event:
                    self.env[constants.MOODLE_IMPORT_STATS_MODEL].create({
                        'new_event': new_imp_event, 'upd_event': upd_imp_event
                    })
            else:
                _logging.error("Moodle Calendar Event Import Error: " + event_response["response"])
        else:
            _logging.error(constants.MDL_CREDENTIALS_NOT_FND)

    def export_events(self):
        _logging = logging.getLogger(__name__)

        credentials = utils.get_moodle_credentials(self_env=self.env)
        if credentials:
            _event = calendar_service.MoodleCalendarService(credentials=credentials, self_env=self.env)
            event_response = _event.export_events()
            if not event_response["err_status"]:
                new_exp_event = event_response["success"]
                if new_exp_event:
                    self.env[constants.MOODLE_EXPORT_STATS_MODEL].create({
                        'new_event': new_exp_event
                    })
            else:
                _logging.error("Moodle Calendar Event Export Error: " + event_response["response"])
        else:
            _logging.error(constants.MDL_CREDENTIALS_NOT_FND)

    ##############################################################################################################
    # #################################      End Default Function Operations     #################################
    ##############################################################################################################

    def write(self, values):
        return super(MoodleCronJobSettings, self).write(values)

    ##############################################################################################################
    # #################################      Cron Import Function Operations     #################################
    ##############################################################################################################

    def update_import_cron_user(self, data):
        _logging = logging.getLogger(__name__)

        delete_query = "delete from {0} where cron_name='{1}';".format(
            constants.IR_CRON_STASH_MODEL, constants.MOODLE_IMPORT_USER_DEF)
        self.env.cr.execute(delete_query)

        chk_exist_cron = self.env[constants.IR_CRON_MODEL].search([
            ('name', '=', constants.MOODLE_IMPORT_USER_DEF)
        ])
        if chk_exist_cron and len(chk_exist_cron) > 0:
            chk_exist_cron[0].write({
                'numbercall': data["import_call_num_user"],
                'active': data["is_auto_import_user"],
                'interval_number': data["import_interval_num_user"],
                'interval_type': data["import_interval_type_user"],
            })
        else:
            self.env[constants.IR_CRON_MODEL].create({
                'name': constants.MOODLE_IMPORT_USER_DEF,
                'model_id': self.env[constants.IR_MODEL_MODEL].search([
                    ("model", "=", constants.MOODLE_CRONJOB_SETTINGS_MODEL)])[0].id,
                'code': 'model.import_users()',
                'numbercall': data["import_call_num_user"],
                'active': data["is_auto_import_user"],
                'interval_number': data["import_interval_num_user"],
                'interval_type': data["import_interval_type_user"],
                'priority': 2,
                'doall': 1
            })

    def update_import_cron_category(self, data):
        _logging = logging.getLogger(__name__)

        delete_query = "delete from {0} where cron_name='{1}';".format(
            constants.IR_CRON_STASH_MODEL, constants.MOODLE_IMPORT_CATEGORY_DEF)
        self.env.cr.execute(delete_query)

        chk_exist_cron = self.env[constants.IR_CRON_MODEL].search([('name', '=', constants.MOODLE_IMPORT_CATEGORY_DEF)])
        if chk_exist_cron and len(chk_exist_cron) > 0:
            chk_exist_cron[0].write({
                'numbercall': data["import_call_num_category"],
                'active': data["is_auto_import_category"],
                'interval_number': data["import_interval_num_category"],
                'interval_type': data["import_interval_type_category"],
            })
        else:
            self.env[constants.IR_CRON_MODEL].create({
                'name': constants.MOODLE_IMPORT_CATEGORY_DEF,
                'model_id': self.env[constants.IR_MODEL_MODEL].search([
                    ("model", "=", constants.MOODLE_CRONJOB_SETTINGS_MODEL)])[0].id,
                'code': 'model.import_categories()',
                'numbercall': data["import_call_num_category"],
                'active': data["is_auto_import_category"],
                'interval_number': data["import_interval_num_category"],
                'interval_type': data["import_interval_type_category"],
                'priority': 2,
                'doall': 1
            })

    def update_import_cron_course(self, data):
        _logging = logging.getLogger(__name__)

        delete_query = "delete from {0} where cron_name='{1}';".format(
            constants.IR_CRON_STASH_MODEL, constants.MOODLE_IMPORT_COURSE_DEF)
        self.env.cr.execute(delete_query)

        chk_exist_cron = self.env[constants.IR_CRON_MODEL].search([('name', '=', constants.MOODLE_IMPORT_COURSE_DEF)])
        if chk_exist_cron and len(chk_exist_cron) > 0:
            chk_exist_cron[0].write({
                'numbercall': data["import_call_num_course"],
                'active': data["is_auto_import_course"],
                'interval_number': data["import_interval_num_course"],
                'interval_type': data["import_interval_type_course"],
            })
        else:
            self.env[constants.IR_CRON_MODEL].create({
                'name': constants.MOODLE_IMPORT_COURSE_DEF,
                'model_id': self.env[constants.IR_MODEL_MODEL].search([
                    ("model", "=", constants.MOODLE_CRONJOB_SETTINGS_MODEL)])[0].id,
                'code': 'model.import_courses()',
                'numbercall': data["import_call_num_course"],
                'active': data["is_auto_import_course"],
                'interval_number': data["import_interval_num_course"],
                'interval_type': data["import_interval_type_course"],
                'priority': 2,
                'doall': 1
            })

    def update_import_cron_event(self, data):
        _logging = logging.getLogger(__name__)

        delete_query = "delete from {0} where cron_name='{1}';".format(
            constants.IR_CRON_STASH_MODEL, constants.MOODLE_IMPORT_EVENT_DEF)
        self.env.cr.execute(delete_query)

        chk_exist_cron = self.env[constants.IR_CRON_MODEL].search([('name', '=', constants.MOODLE_IMPORT_EVENT_DEF)])
        if chk_exist_cron and len(chk_exist_cron) > 0:
            chk_exist_cron[0].write({
                'numbercall': data["import_call_num_event"],
                'active': data["is_auto_import_event"],
                'interval_number': data["import_interval_num_event"],
                'interval_type': data["import_interval_type_event"],
            })
        else:
            self.env[constants.IR_CRON_MODEL].create({
                'name': constants.MOODLE_IMPORT_EVENT_DEF,
                'model_id': self.env[constants.IR_MODEL_MODEL].search([
                    ("model", "=", constants.MOODLE_CRONJOB_SETTINGS_MODEL)])[0].id,
                'code': 'model.import_events()',
                'numbercall': data["import_call_num_event"],
                'active': data["is_auto_import_event"],
                'interval_number': data["import_interval_num_event"],
                'interval_type': data["import_interval_type_event"],
                'priority': 2,
                'doall': 1
            })

    ##############################################################################################################
    # #################################      Cron Export Function Operations     #################################
    ##############################################################################################################

    def update_export_cron_user(self, data):
        _logging = logging.getLogger(__name__)

        delete_query = "delete from {0} where cron_name='{1}';".format(
            constants.IR_CRON_STASH_MODEL, constants.MOODLE_EXPORT_USER_DEF)
        self.env.cr.execute(delete_query)

        chk_exist_cron = self.env[constants.IR_CRON_MODEL].search([('name', '=', constants.MOODLE_EXPORT_USER_DEF)])
        if chk_exist_cron and len(chk_exist_cron) > 0:
            chk_exist_cron[0].write({
                'numbercall': data["export_call_num_user"],
                'active': data["is_auto_export_user"],
                'interval_number': data["export_interval_num_user"],
                'interval_type': data["export_interval_type_user"]
            })
        else:
            self.env[constants.IR_CRON_MODEL].create({
                'name': constants.MOODLE_EXPORT_USER_DEF,
                'model_id': self.env[constants.IR_MODEL_MODEL].search([
                    ("model", "=", constants.MOODLE_CRONJOB_SETTINGS_MODEL)])[0].id,
                'code': 'model.export_users()',
                'numbercall': data["export_call_num_user"],
                'active': data["is_auto_export_user"],
                'interval_number': data["export_interval_num_user"],
                'interval_type': data["export_interval_type_user"],
                'priority': 1
            })

    def update_export_cron_category(self, data):
        _logging = logging.getLogger(__name__)

        delete_query = "delete from {0} where cron_name='{1}';".format(
            constants.IR_CRON_STASH_MODEL, constants.MOODLE_EXPORT_CATEGORY_DEF)
        self.env.cr.execute(delete_query)

        chk_exist_cron = self.env[constants.IR_CRON_MODEL].search([('name', '=', constants.MOODLE_EXPORT_CATEGORY_DEF)])
        if chk_exist_cron and len(chk_exist_cron) > 0:
            chk_exist_cron[0].write({
                'numbercall': data["export_call_num_category"],
                'active': data["is_auto_export_category"],
                'interval_number': data["export_interval_num_category"],
                'interval_type': data["export_interval_type_category"]
            })
        else:
            self.env[constants.IR_CRON_MODEL].create({
                'name': constants.MOODLE_EXPORT_CATEGORY_DEF,
                'model_id': self.env[constants.IR_MODEL_MODEL].search([
                    ("model", "=", constants.MOODLE_CRONJOB_SETTINGS_MODEL)])[0].id,
                'code': 'model.export_categories()',
                'numbercall': data["export_call_num_category"],
                'active': data["is_auto_export_category"],
                'interval_number': data["export_interval_num_category"],
                'interval_type': data["export_interval_type_category"],
                'priority': 1
            })

    def update_export_cron_course(self, data):
        _logging = logging.getLogger(__name__)

        delete_query = "delete from {0} where cron_name='{1}';".format(
            constants.IR_CRON_STASH_MODEL, constants.MOODLE_EXPORT_COURSE_DEF)
        self.env.cr.execute(delete_query)

        chk_exist_cron = self.env[constants.IR_CRON_MODEL].search([('name', '=', constants.MOODLE_EXPORT_COURSE_DEF)])
        if chk_exist_cron and len(chk_exist_cron) > 0:
            chk_exist_cron[0].write({
                'numbercall': data["export_call_num_course"],
                'active': data["is_auto_export_course"],
                'interval_number': data["export_interval_num_course"],
                'interval_type': data["export_interval_type_course"]
            })
        else:
            self.env[constants.IR_CRON_MODEL].create({
                'name': constants.MOODLE_EXPORT_COURSE_DEF,
                'model_id': self.env[constants.IR_MODEL_MODEL].search([
                    ("model", "=", constants.MOODLE_CRONJOB_SETTINGS_MODEL)])[0].id,
                'code': 'model.export_courses()',
                'numbercall': data["export_call_num_course"],
                'active': data["is_auto_export_course"],
                'interval_number': data["export_interval_num_course"],
                'interval_type': data["export_interval_type_course"],
                'priority': 1
            })

    def update_export_cron_event(self, data):
        _logging = logging.getLogger(__name__)

        delete_query = "delete from {0} where cron_name='{1}';".format(
            constants.IR_CRON_STASH_MODEL, constants.MOODLE_EXPORT_EVENT_DEF)
        self.env.cr.execute(delete_query)

        chk_exist_cron = self.env[constants.IR_CRON_MODEL].search([('name', '=', constants.MOODLE_EXPORT_EVENT_DEF)])
        if chk_exist_cron and len(chk_exist_cron) > 0:
            chk_exist_cron[0].write({
                'numbercall': data["export_call_num_event"],
                'active': data["is_auto_export_event"],
                'interval_number': data["export_interval_num_event"],
                'interval_type': data["export_interval_type_event"],
            })
        else:
            self.env[constants.IR_CRON_MODEL].create({
                'name': constants.MOODLE_EXPORT_EVENT_DEF,
                'model_id': self.env[constants.IR_MODEL_MODEL].search([
                    ("model", "=", constants.MOODLE_CRONJOB_SETTINGS_MODEL)])[0].id,
                'code': 'model.export_events()',
                'numbercall': data["export_call_num_event"],
                'active': data["is_auto_export_event"],
                'interval_number': data["export_interval_num_event"],
                'interval_type': data["export_interval_type_event"],
                'priority': 2,
                'doall': 1
            })
            
    ####################################################################################################
    # ###################      End Cron Import / Export Function Operations     ########################
    ####################################################################################################

    def save_config_mod(self):
        _logging = logging.getLogger(__name__)

        rep_message = ''
        data_db_struct = {
            'is_auto_import_user': self.is_auto_import_user,
            'import_interval_num_user': self.import_interval_num_user,
            'import_call_num_user': self.import_call_num_user,
            'import_interval_type_user': self.import_interval_type_user,
            'is_auto_export_user': self.is_auto_export_user,
            'export_interval_num_user': self.export_interval_num_user,
            'export_call_num_user': self.export_call_num_user,
            'export_interval_type_user': self.export_interval_type_user,

            'is_auto_import_category': self.is_auto_import_category,
            'import_interval_num_category': self.import_interval_num_category,
            'import_call_num_category': self.import_call_num_category,
            'import_interval_type_category': self.import_interval_type_category,
            'is_auto_export_category': self.is_auto_export_category,
            'export_interval_num_category': self.export_interval_num_category,
            'export_call_num_category': self.export_call_num_category,
            'export_interval_type_category': self.export_interval_type_category,

            'is_auto_import_course': self.is_auto_import_course,
            'import_interval_num_course': self.import_interval_num_course,
            'import_call_num_course': self.import_call_num_course,
            'import_interval_type_course': self.import_interval_type_course,
            'is_auto_export_course': self.is_auto_export_course,
            'export_interval_num_course': self.export_interval_num_course,
            'export_call_num_course': self.export_call_num_course,
            'export_interval_type_course': self.export_interval_type_course,

            'is_auto_import_event': self.is_auto_import_event,
            'import_interval_num_event': self.import_interval_num_event,
            'import_call_num_event': self.import_call_num_event,
            'import_interval_type_event': self.import_interval_type_event,
            'is_auto_export_event': self.is_auto_export_event,
            'export_interval_num_event': self.export_interval_num_event,
            'export_call_num_event': self.export_call_num_event,
            'export_interval_type_event': self.export_interval_type_event  
        }
        try:
            db_rows = self.env[self._name].search([])
            if db_rows and len(db_rows) > 0:
                _logging.info("Update Cron Job record")
                # if db_rows[constants.INITIAL_INDEX]:
                db_rows[constants.INITIAL_INDEX].write(data_db_struct)
                rep_message += constants.MDL_CRON_UPDATE
            else:
                _logging.info("Create Cron Job record")
                super().create(data_db_struct)
                rep_message += constants.MDL_CRON_CREATE

            self.update_import_cron_user(data=data_db_struct)
            self.update_export_cron_user(data=data_db_struct)
            self.update_import_cron_category(data=data_db_struct)
            self.update_export_cron_category(data=data_db_struct)

            self.update_import_cron_course(data=data_db_struct)
            self.update_export_cron_course(data=data_db_struct)
            self.update_import_cron_event(data=data_db_struct)
            self.update_export_cron_event(data=data_db_struct)

        except Exception as ex:
            _logging.exception("Moodle CronJob Configuration Exception: " + str(ex))
            rep_message += constants.MDL_CRON_EXCEPT
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "System Notification",
                'message': rep_message,
                'sticky': False,
            }
        }

    ##############################################################################################################
    # ##################################      For Users Default Operations     ################################
    ##############################################################################################################

    @api.model
    def get_auto_import_status_user(self):
        db_rows = self.env[self._name].search([('is_auto_import_user', "=", True)])
        return db_rows[constants.INITIAL_INDEX].is_auto_import_user if len(db_rows) > 0 else False

    @api.model
    def get_auto_export_status_user(self):
        db_rows = self.env[self._name].search([('is_auto_export_user', "=", True)])
        return db_rows[constants.INITIAL_INDEX].is_auto_export_user if len(db_rows) > 0 else False

    @api.model
    def get_import_interval_num_user(self):
        db_rows = self.env[self._name].search([])
        return int(db_rows[constants.INITIAL_INDEX].import_interval_num_user) \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].import_interval_num_user else 1

    @api.model
    def get_export_interval_num_user(self):
        db_rows = self.env[self._name].search([])
        return int(db_rows[constants.INITIAL_INDEX].export_interval_num_user) \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].export_interval_num_user else 1

    @api.model
    def get_import_call_num_user(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].import_call_num_user \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].import_call_num_user else '1'

    @api.model
    def get_export_call_num_user(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].export_call_num_user \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].export_call_num_user else '1'

    @api.model
    def get_import_interval_type_user(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].import_interval_type_user \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].import_interval_type_user else 'minutes'

    @api.model
    def get_export_interval_type_user(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].export_interval_type_user \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].export_interval_type_user else 'minutes'

    ##############################################################################################################
    # ##################################      For Category Default Operations     ################################
    ##############################################################################################################

    @api.model
    def get_auto_import_status_category(self):
        db_rows = self.env[self._name].search([('is_auto_import_category', "=", True)])
        return db_rows[constants.INITIAL_INDEX].is_auto_import_category if len(db_rows) > 0 else False

    @api.model
    def get_auto_export_status_category(self):
        db_rows = self.env[self._name].search([('is_auto_import_category', "=", True)])
        return db_rows[constants.INITIAL_INDEX].is_auto_import_category if len(db_rows) > 0 else False

    @api.model
    def get_import_interval_num_category(self):
        db_rows = self.env[self._name].search([])
        return int(db_rows[constants.INITIAL_INDEX].import_interval_num_category) \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].import_interval_num_category else 1

    @api.model
    def get_export_interval_num_category(self):
        db_rows = self.env[self._name].search([])
        return int(db_rows[constants.INITIAL_INDEX].export_interval_num_category) \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].export_interval_num_category else 1

    @api.model
    def get_import_call_num_category(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].import_call_num_category \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].import_call_num_category else '1'

    @api.model
    def get_export_call_num_category(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].export_call_num_category \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].export_call_num_category else '1'

    @api.model
    def get_import_interval_type_category(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].import_interval_type_category \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].import_interval_type_category else 'minutes'

    @api.model
    def get_export_interval_type_category(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].export_interval_type_category \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].export_interval_type_category else 'minutes'

    #############################################################################################################
    # #################################      For Courses Default Operations     #################################
    #############################################################################################################

    @api.model
    def get_auto_import_status_course(self):
        db_rows = self.env[self._name].search([('is_auto_import_course', "=", True)])
        return db_rows[constants.INITIAL_INDEX].is_auto_import_course if len(db_rows) > 0 else False

    @api.model
    def get_auto_export_status_course(self):
        db_rows = self.env[self._name].search([('is_auto_import_course', "=", True)])
        return db_rows[constants.INITIAL_INDEX].is_auto_import_course if len(db_rows) > 0 else False

    @api.model
    def get_import_interval_num_course(self):
        db_rows = self.env[self._name].search([])
        return int(db_rows[constants.INITIAL_INDEX].import_interval_num_course) \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].import_interval_num_course else 1

    @api.model
    def get_export_interval_num_course(self):
        db_rows = self.env[self._name].search([])
        return int(db_rows[constants.INITIAL_INDEX].export_interval_num_course) \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].export_interval_num_course else 1

    @api.model
    def get_import_call_num_course(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].import_call_num_course \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].import_call_num_course else '1'

    @api.model
    def get_export_call_num_course(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].export_call_num_course \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].export_call_num_course else '1'

    @api.model
    def get_import_interval_type_course(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].import_interval_type_course \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].import_interval_type_course else 'minutes'

    @api.model
    def get_export_interval_type_course(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].export_interval_type_course \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].export_interval_type_course else 'minutes'

    ##############################################################################################################
    # ###################################      For Events Default Operations      ################################
    ##############################################################################################################

    @api.model
    def get_auto_import_status_event(self):
        db_rows = self.env[self._name].search([('is_auto_import_event', "=", True)])
        return db_rows[constants.INITIAL_INDEX].is_auto_import_event if len(db_rows) > 0 else False

    @api.model
    def get_auto_export_status_event(self):
        db_rows = self.env[self._name].search([('is_auto_export_event', "=", True)])
        return db_rows[constants.INITIAL_INDEX].is_auto_export_event if len(db_rows) > 0 else False

    @api.model
    def get_import_interval_num_event(self):
        db_rows = self.env[self._name].search([])
        return int(db_rows[constants.INITIAL_INDEX].import_interval_num_event) \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].import_interval_num_event else 1

    @api.model
    def get_export_interval_num_event(self):
        db_rows = self.env[self._name].search([])
        return int(db_rows[constants.INITIAL_INDEX].export_interval_num_event) \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].export_interval_num_event else 1

    @api.model
    def get_import_call_num_event(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].import_call_num_event \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].import_call_num_event else '1'

    @api.model
    def get_export_call_num_event(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].export_call_num_event \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].export_call_num_event else '1'

    @api.model
    def get_import_interval_type_event(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].import_interval_type_event \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].import_interval_type_event else 'minutes'

    @api.model
    def get_export_interval_type_event(self):
        db_rows = self.env[self._name].search([])
        return db_rows[constants.INITIAL_INDEX].export_interval_type_event \
            if len(db_rows) > 0 and db_rows[constants.INITIAL_INDEX].export_interval_type_event else 'minutes'
