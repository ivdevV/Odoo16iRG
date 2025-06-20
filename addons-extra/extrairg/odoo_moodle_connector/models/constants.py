#################################################################################################################
# ########################################      Moodle Basics       #############################################
#################################################################################################################

BASE_WEBSERVICE_URL = '{0}/webservice/rest/server.php'
REQ_TIMEOUT = 60

SLIDE_CHANNEL_MODEL = 'slide.channel'
SLIDE_CHANNEL_PARTNER_MODEL = 'slide.channel.partner'
RES_PARTNER_MODEL = 'res.partner'
RES_PARTNER_CATEGORY_MODEL = 'res.partner.category'
CALENDAR_EVENT_MODEL = 'calendar.event'
COURSE_SELECTION_MODEL = 'course.selection'
CATEGORY_SELECTION_MODEL = 'category.selection'
RES_LANG_MODEL = 'res.lang'
IR_CRON_MODEL = 'ir.cron'
IR_CRON_STASH_MODEL = 'ir_cron'
IR_MODEL_MODEL = 'ir.model'
HR_DEPARTMENT_MODEL = 'hr.department'
RES_COUNTRY_MODEL = 'res.country'
RES_COUNTRY_STATE_MODEL = 'res.country.state'

MOODLE_CREDENTIALS_MODEL = 'moodle.credentials'
MOODLE_CONNECTOR_MODEL = 'moodle.connector'
MOODLE_IMPORT_STATS_MODEL = 'moodle.import.stats'
MOODLE_EXPORT_STATS_MODEL = 'moodle.export.stats'
MOODLE_CRONJOB_SETTINGS_MODEL = 'moodle.cronjob.settings'

MOODLE_CATEGORIES_MODEL = 'moodle.categories'
MOODLE_INSTITUTION_MODEL = 'moodle.institution'
MOODLE_INTEREST_MODEL = 'moodle.interest'
MOODLE_INTEREST_MODEL_REF = 'moodle_interest_rel'

MOODLE_CREDENTIALS_MODEL_DESC = 'moodle.credentials Description'
MOODLE_CONNECTOR_MODEL_DESC = 'moodle.connector Description'
MOODLE_IMPORT_STATS_MODEL_DESC = 'moodle.import.stats Description'
MOODLE_EXPORT_STATS_MODEL_DESC = 'moodle.export.stats Description'
MOODLE_CRONJOB_SETTINGS_MODEL_DESC = 'moodle.cronjob.settings Description'

MOODLE_CATEGORIES_MODEL_DESC = 'moodle.categories Description'
MOODLE_INSTITUTION_MODEL_DESC = 'moodle.institution Description'
MOODLE_INTEREST_MODEL_DESC = 'moodle.interest Description'

MOODLE_IMPORT_USER_DEF = 'Moodle Import Users'
MOODLE_IMPORT_CATEGORY_DEF = 'Moodle Import Categories'
MOODLE_IMPORT_COURSE_DEF = 'Moodle Import Courses'
MOODLE_IMPORT_EVENT_DEF = 'Moodle Import Events'
MOODLE_EXPORT_USER_DEF = 'Moodle Export Users'
MOODLE_EXPORT_CATEGORY_DEF = 'Moodle Export Categories'
MOODLE_EXPORT_COURSE_DEF = 'Moodle Export Courses'
MOODLE_EXPORT_EVENT_DEF = 'Moodle Export Events'

#################################################################################################################
# ########################################  Course Categories  ##################################################
#################################################################################################################

MDL_CATEGORY_CREATE_FUNC = 'core_course_create_categories'
MDL_CATEGORY_GET_ALL_FUNC = 'core_course_get_categories'
MDL_CATEGORY_UPDATE_FUNC = 'core_course_update_categories'
MDL_CATEGORY_DELETE_FUNC = 'core_course_delete_categories'

MDL_CATEGORY_WEB_SERV_IMPORT_ERR = 'Oops, Unable to fetch categories from cloud, Please try again.'
MDL_CATEGORY_WEB_SERV_IMPORT_EXCEPT = 'Oops, Unable to process categories from cloud, Please try again.'
MDL_CATEGORY_IMPORT_NOT_FND = 'Oops, no categories found, Please try again.'
MDL_CATEGORY_WEB_IMPORT_EXCEPT = 'Oops, import categories to Odoo failed, Please try again.'

MDL_CATEGORY_WEB_SERV_EXPORT_EXCEPT = 'Oops, export categories to cloud server failed, Please try again.'
MDL_CATEGORY_WEB_EXPORT_FAIL = 'Oops, Unable to export categories to cloud, Please try again.'
MDL_CATEGORY_WEB_EXPORT_NOT_FND = 'Oops, no categories are found for export operation. Please try again.'
MDL_CATEGORY_WEB_EXPORT_EXCEPT = 'Oops, Unable to process categories to cloud, Please try again.'

MDL_CATEGORY_CRT_ERR = 'Oops, unable to create/update category in local/server. Please try again.'
MDL_CATEGORY_CRT_EXCEPT = 'Oops, create/update category in local/server failed. Please try again.'
MDL_CATEGORY_CHK_ERR = 'Oops, unable to check category in local/server. Please try again.'
MDL_CATEGORY_CHK_EXCEPT = 'Oops, check category in local/server failed. Please try again.'
MDL_CATEGORY_DEL_ERR = 'Oops, unable to delete category in local/server. Please try again.'
MDL_CATEGORY_DEL_EXCEPT = 'Oops, delete category in local/server failed. Please try again.'

#################################################################################################################
# ##############################################     Courses     ################################################
#################################################################################################################

MDL_COURSE_GET_ALL_FUNC = 'core_course_get_courses'
MDL_COURSE_CREATE_FUNC = 'core_course_create_courses'
MDL_COURSE_SEARCH_FUNC = 'core_course_search_courses'
MDL_COURSE_UPDATE_FUNC = 'core_course_update_courses'
MDL_COURSE_DELETE_FUNC = 'core_course_delete_courses'

MDL_COURSE_WEB_SERV_IMPORT_ERR = 'Oops, Unable to fetch courses from cloud, Please try again.'
MDL_COURSE_WEB_SERV_IMPORT_EXCEPT = 'Oops, Unable to process courses from cloud, Please try again.'
MDL_COURSE_IMPORT_NOT_FND = 'Oops, no courses found, Please try again.'
MDL_COURSE_WEB_IMPORT_EXCEPT = 'Oops, import courses to Odoo failed, Please try again.'

MDL_COURSE_WEB_SERV_EXPORT_EXCEPT = 'Oops, export courses to cloud server failed, Please try again.'
MDL_COURSE_WEB_EXPORT_FAIL = 'Oops, Unable to export courses to cloud, Please try again.'
MDL_COURSE_WEB_EXPORT_NOT_FND = 'Oops, no courses are found for export operation. Please try again.'
MDL_COURSE_WEB_EXPORT_EXCEPT = 'Oops, Unable to process courses to cloud, Please try again.'

MDL_COURSE_CRT_ERR = 'Oops, unable to create/update course in local/server. Please try again.'
MDL_COURSE_CRT_EXCEPT = 'Oops, create/update course in local/server failed. Please try again.'
MDL_COURSE_CHK_ERR = 'Oops, unable to check course in local/server. Please try again.'
MDL_COURSE_CHK_EXCEPT = 'Oops, check course in local/server failed. Please try again.'
MDL_COURSE_DEL_ERR = 'Oops, unable to delete course in local/server. Please try again.'
MDL_COURSE_DEL_EXCEPT = 'Oops, delete course in local/server failed. Please try again.'

#################################################################################################################
# ###########################################     Students     ##################################################
#################################################################################################################

MDL_USER_CREATE_FUNC = 'core_user_create_users'
MDL_USER_GET_ALL_FUNC = 'core_user_get_users'
MDL_USER_UPDATE_FUNC = 'core_user_update_users'
MDL_USER_DELETE_FUNC = 'core_user_delete_users'
MDL_FILE_UPLOAD_FUNC = 'core_files_upload'
MDL_USER_UPDATE_IMG_FUNC = 'core_user_update_picture'
MDL_USER_ENROL_FUNC = 'enrol_manual_enrol_users'
MDL_USER_UNENROL_FUNC = 'enrol_manual_unenrol_users'
MDL_USER_GET_USERS_BY_COURSE_FUNC = 'core_enrol_get_enrolled_users'

MDL_USER_CRT_ERR = 'Oops, unable to create/update user in local/server. Please try again.'
MDL_USER_CRT_EXCEPT = 'Oops, create/update user in local/server failed. Please try again.'
MDL_USER_CHK_ERR = 'Oops, unable to check user in local/server. Please try again.'
MDL_USER_CHK_EXCEPT = 'Oops, check user in local/server failed. Please try again.'
MDL_USER_DEL_ERR = 'Oops, unable to delete user in local/server. Please try again.'
MDL_USER_DEL_EXCEPT = 'Oops, delete user in local/server failed. Please try again.'

MDL_USER_UPD_IMG_ERR = 'Oops, unable to update user. Please try again.'
MDL_USER_UPD_IMG_EXCEPT = 'Oops, update user image failed. Please try again.'
MDL_USER_UPLOAD_IMG_ERR = 'Oops, unable to upload image of user. Please try again.'
MDL_USER_UPLOAD_IMG_EXCEPT = 'Oops, upload user image failed. Please try again.'

MDL_USER_WEB_SERV_IMPORT_NOT_FND = 'Oops, no users found from server import. Please try again.'
MDL_USER_WEB_SERV_IMPORT_ERR = 'Oops, unable to import users from server. Please try again.'
MDL_USER_WEB_SERV_IMPORT_EXCEPT = 'Oops, users import from server failed. Please try again.'
MDL_USER_WEB_IMPORT_NOT_FND = 'Oops, no users found for import. Please try again.'
MDL_USER_WEB_IMPORT_ERR = 'Oops, unable to import users. Please try again.'
MDL_USER_WEB_IMPORT_EXCEPT = 'Oops, users import failed. Please try again.'

MDL_USER_WEB_SERV_EXPORT_NOT_FND = 'Oops, no users found for server export. Please try again.'
MDL_USER_WEB_SERV_EXPORT_ERR = 'Oops, unable to export users to server. Please try again.'
MDL_USER_WEB_SERV_EXPORT_EXCEPT = 'Oops, users export to server failed. Please try again.'
MDL_USER_WEB_EXPORT_NOT_FND = 'Oops, no users found for export. Please try again.'
MDL_USER_WEB_EXPORT_ERR = 'Oops, unable to export users. Please try again.'
MDL_USER_WEB_EXPORT_EXCEPT = 'Oops, users export failed. Please try again.'

MDL_USER_GET_ALL_BY_COURSE_ERR = 'Oops, unable to get enrolled users by course. Please try again.'
MDL_USER_GET_ALL_BY_COURSE_EXCEPT = 'Oops, get enrolled users by course failed. Please try again.'
MDL_USER_ENROL_BY_COURSE_ERR = 'Oops, unable to enrolled users by course. Please try again.'
MDL_USER_ENROL_BY_COURSE_EXCEPT = 'Oops, enrolled users by course failed. Please try again.'
MDL_USER_UNENROL_BY_COURSE_ERR = 'Oops, unable to unenrolled users by course. Please try again.'
MDL_USER_UNENROL_BY_COURSE_EXCEPT = 'Oops, unenrolled users by course failed. Please try again.'

#################################################################################################################
# #############################################     Calendar     ################################################
#################################################################################################################

MDL_CALENDAR_EVENT_CREATE_FUNC = 'core_calendar_create_calendar_events'
MDL_CALENDAR_EVENT_DELETE_FUNC = 'core_calendar_delete_calendar_events'
MDL_CALENDAR_EVENT_GET_BY_ID_FUNC = 'core_calendar_get_calendar_event_by_id'
MDL_CALENDAR_EVENT_GET_ALL_FUNC = 'core_calendar_get_calendar_events'
MDL_CALENDAR_EVENT_GET_BY_COURSE_FUNC = 'core_calendar_get_action_events_by_course'

MDL_CALENDAR_EVENT_WEB_SERV_IMPORT_NOT_FND = 'Oops, no calendar events found from server import. Please try again.'
MDL_CALENDAR_EVENT_WEB_SERV_IMPORT_ERR = 'Oops, unable to import calendar events from server. Please try again.'
MDL_CALENDAR_EVENT_WEB_SERV_IMPORT_EXCEPT = 'Oops, calendar events import from server failed. Please try again.'
MDL_CALENDAR_EVENT_WEB_IMPORT_NOT_FND = 'Oops, no calendar events found for import. Please try again.'
MDL_CALENDAR_EVENT_WEB_IMPORT_ERR = 'Oops, unable to import calendar events. Please try again.'
MDL_CALENDAR_EVENT_WEB_IMPORT_EXCEPT = 'Oops, calendar events import failed. Please try again.'

MDL_CALENDAR_EVENT_WEB_SERV_EXPORT_NOT_FND = 'Oops, no calendar events found for server export. Please try again.'
MDL_CALENDAR_EVENT_WEB_SERV_EXPORT_ERR = 'Oops, unable to export calendar events to server. Please try again.'
MDL_CALENDAR_EVENT_WEB_SERV_EXPORT_EXCEPT = 'Oops, calendar events export to server failed. Please try again.'
MDL_CALENDAR_EVENT_WEB_EXPORT_NOT_FND = 'Oops, no calendar events found for export. Please try again.'
MDL_CALENDAR_EVENT_WEB_EXPORT_ERR = 'Oops, unable to export calendar events. Please try again.'
MDL_CALENDAR_EVENT_WEB_EXPORT_EXCEPT = 'Oops, calendar events export failed. Please try again.'

MDL_CALENDAR_EVENT_CRT_ERR = 'Oops, unable to create calendar event local/server. Please try again'
MDL_CALENDAR_EVENT_CRT_EXCEPT = 'Oops, create calendar event failed local/server. Please try again'
MDL_CALENDAR_EVENT_CHK_ERR = 'Oops, unable to check calendar event local/server. Please try again'
MDL_CALENDAR_EVENT_CHK_EXCEPT = 'Oops, check calendar event failed local/server. Please try again'
MDL_CALENDAR_EVENT_DEL_ERR = 'Oops, unable to delete calendar event local/server. Please try again'
MDL_CALENDAR_EVENT_DEL_EXCEPT = 'Oops, delete calendar event failed local/server. Please try again'

#################################################################################################################
# #############################################     Configure     ###############################################
#################################################################################################################

WEB_TOKEN_FIELD = 'wstoken'
WEB_FUNCTION_FIELD = 'wsfunction'
WEB_FORMAT_FIELD = 'moodlewsrestformat'
WEB_ERROR_FIELD = 'errorcode'
DEFAULT_FORMAT = 'json'

MDL_CREDENTIALS_NOT_LCT = 'Oops, unable to locate credentials, Please try again.'
MDL_CREDENTIALS_NOT_FND = 'Oops, credentials not found, Please try again.'
MDL_CREDENTIALS_LCT_EXCEPT = 'Oops, credentials searching failed, Please try again.'
MDL_CREDENTIALS_CNT_EXCEPT = 'Oops, moodle credentials creating/updating failed, Please try again.'
MDL_CREDENTIALS_CNT_SUC = 'Moodle Credentials saved successfully'

MDL_CONNECTOR_SYNC_ERR = 'Oops, unable to synchronize for selected features, Please try again.'
MDL_CONNECTOR_SYNC_EXCEPT = 'Oops, something went wrong during synchronization. Please try again.'
MDL_SYNC_PROCESS_MSG = 'Synchronization process completed successfully'
MDL_NO_OPT_SECTION_ERR = 'Please select any feature option before synchronization process'

INITIAL_INDEX = 0
DEFAULT_INDEX = -1

RESPONSE_ERROR_KEY = 'error'
RESPONSE_EXCEPTION_KEY = 'exception'
RESPONSE_MESSAGE_KEY = 'message'
RESPONSE_ERR_MESSAGE_KEY = 'err_message'

MDL_CRON_CREATE = 'Moodle CronJob settings are created successfully'
MDL_CRON_UPDATE = 'Moodle CronJob settings are updated successfully'
MDL_CRON_EXCEPT = 'Oops, unable to save Moodle CronJob settings. Please try again'
