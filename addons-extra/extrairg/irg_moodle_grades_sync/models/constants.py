# Moodle Web Service function names + local model refs for grade sync.
# The odoo_moodle_connector module already exposes BASE_WEBSERVICE_URL and the
# credentials/service pattern; here we only add the grade-specific pieces.

REQ_TIMEOUT = 60
BASE_WEBSERVICE_URL = '{0}/webservice/rest/server.php'

# Moodle WS functions
MDL_GRADE_GET_ITEMS_FUNC = 'gradereport_user_get_grade_items'
MDL_GRADE_GET_GRADES_FUNC = 'core_grades_get_grades'
MDL_COURSE_GET_ALL_FUNC = 'core_course_get_courses'
MDL_ENROL_GET_USERS_FUNC = 'core_enrol_get_enrolled_users'

# Moodle response error markers (same convention as the connector)
RESPONSE_ERROR_KEY = 'error'
RESPONSE_EXCEPTION_KEY = 'exception'

# Local Odoo models
OP_STUDENT_MODEL = 'op.student'
OP_SUBJECT_MODEL = 'op.subject'
RES_PARTNER_MODEL = 'res.partner'
SUBJECT_MAP_MODEL = 'irg.moodle.subject.map'
STUDENT_MAP_MODEL = 'irg.moodle.student.map'
GRADE_MODEL = 'irg.moodle.grade'
