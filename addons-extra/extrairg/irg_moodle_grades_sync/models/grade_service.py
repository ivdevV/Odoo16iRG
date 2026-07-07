import logging
import requests

from . import constants

_logger = logging.getLogger(__name__)


class MoodleGradeService:
    """Thin client over the Moodle Web Services grade report.

    Mirrors the service-class pattern used by odoo_moodle_connector
    (user_service.py / course_service.py): built from a credentials dict
    ({'access_token', 'base_url'}) and issues POST requests to the REST
    endpoint.
    """

    def __init__(self, credentials, self_env):
        self.__credentials = credentials
        self.__self_env = self_env
        self.__req_timeout = constants.REQ_TIMEOUT
        self.__req_endpoint = constants.BASE_WEBSERVICE_URL.format(credentials['base_url'])
        self.__default_params = {
            'wstoken': credentials['access_token'],
            'wsfunction': '',
            'moodlewsrestformat': 'json',
        }

    def _call(self, wsfunction, data):
        """POST to Moodle. Returns (payload, error_str)."""
        params = dict(self.__default_params)
        params['wsfunction'] = wsfunction
        try:
            resp = requests.post(
                self.__req_endpoint, params=params, data=data,
                timeout=self.__req_timeout).json()
        except Exception as ex:
            _logger.exception('Moodle grade WS call failed (%s): %s', wsfunction, ex)
            return None, 'request_exception'
        if isinstance(resp, dict) and (
                constants.RESPONSE_ERROR_KEY in resp or
                constants.RESPONSE_EXCEPTION_KEY in resp):
            _logger.error('Moodle WS %s returned error: %s', wsfunction, resp)
            return None, resp.get('message') or resp.get('error') or 'ws_error'
        return resp, None

    def get_all_courses(self):
        """Return list of {id, fullname, shortname} for every Moodle course."""
        payload, err = self._call(constants.MDL_COURSE_GET_ALL_FUNC, {})
        if err or not isinstance(payload, list):
            return []
        courses = []
        for course in payload:
            # course id 1 is the Moodle site front page, not a real course.
            if course.get('id') and course.get('id') != 1:
                courses.append({
                    'id': course['id'],
                    'fullname': course.get('fullname') or '',
                    'shortname': course.get('shortname') or '',
                })
        return courses

    def get_enrolled_emails(self, moodle_course_id):
        """Return {moodle_user_id: email} for users enrolled in a course.

        gradereport_user_get_grade_items does not include the email, which is a
        key matching signal, so we enrich it from the enrolment endpoint.
        """
        payload, err = self._call(
            constants.MDL_ENROL_GET_USERS_FUNC, {'courseid': moodle_course_id})
        emails = {}
        if err or not isinstance(payload, list):
            return emails
        for user in payload:
            if user.get('id'):
                emails[user['id']] = (user.get('email') or '').strip()
        return emails

    def get_course_final_grades(self, moodle_course_id):
        """Return final course grade per enrolled user for a Moodle course.

        Uses gradereport_user_get_grade_items and extracts the grade item whose
        itemtype == 'course' (the course total). Email is enriched from the
        enrolment endpoint.

        Returns a list of dicts:
            {moodle_user_id, fullname, email, grade_raw, grade_numeric,
             grade_max, grade_percentage}
        """
        payload, err = self._call(
            constants.MDL_GRADE_GET_ITEMS_FUNC, {'courseid': moodle_course_id})
        if err or not isinstance(payload, dict):
            return []
        emails = self.get_enrolled_emails(moodle_course_id)
        results = []
        for usergrade in payload.get('usergrades', []):
            course_item = None
            for item in usergrade.get('gradeitems', []):
                if item.get('itemtype') == 'course':
                    course_item = item
                    break
            if course_item is None:
                continue
            user_id = usergrade.get('userid')
            results.append({
                'moodle_user_id': user_id,
                'fullname': usergrade.get('userfullname') or '',
                'email': emails.get(user_id, ''),
                'grade_raw': course_item.get('gradeformatted')
                or course_item.get('graderaw'),
                'grade_numeric': course_item.get('graderaw'),
                'grade_max': course_item.get('grademax'),
                'grade_percentage': course_item.get('percentageformatted'),
            })
        return results
