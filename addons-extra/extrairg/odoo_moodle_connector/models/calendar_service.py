from datetime import datetime, timedelta
from . import course_service
from . import constants
import requests
import logging


class MoodleCalendarService:
    def __init__(self, credentials, self_env, initial_date=None, end_date=None):
        self.__logging = logging.getLogger(__name__)

        self.__credentials = credentials
        self.__self_env = self_env
        self.__initial_date = initial_date
        self.__end_date = end_date

        self.__course_object = course_service.MoodleCourseService(
            credentials=credentials, self_env=self_env, initial_date=initial_date, end_date=end_date)
        self.__req_timeout = constants.REQ_TIMEOUT
        self.__req_endpoint = constants.BASE_WEBSERVICE_URL.format(self.__credentials['base_url'])

        self.__get_all_calendar_events_func = constants.MDL_CALENDAR_EVENT_GET_ALL_FUNC
        self.__get_by_id_calendar_event_func = constants.MDL_CALENDAR_EVENT_GET_BY_ID_FUNC
        self.__create_calendar_event_func = constants.MDL_CALENDAR_EVENT_CREATE_FUNC
        self.__delete_calendar_event_func = constants.MDL_CALENDAR_EVENT_DELETE_FUNC
        self.__get_calendar_event_by_course_func = constants.MDL_CALENDAR_EVENT_GET_BY_COURSE_FUNC

        self.__default_params = {
            'wstoken': self.__credentials["access_token"],
            'wsfunction': '',
            'moodlewsrestformat': 'json',
        }
        self.__js_response = {
            'err_status': True,
            'response': None,
            'total': 0,
            'success': 0,
            'updated': 0,
            'failed': 0
        }

    def reset_response(self):
        self.__js_response['err_status'] = True
        self.__js_response['response'] = None
        self.__js_response['total'] = 0
        self.__js_response['success'] = 0
        self.__js_response['updated'] = 0
        self.__js_response['failed'] = 0

    def delete_event(self, l2s_event):
        del_resp = {"err_status": True, "response": None}
        try:
            rm_data = {
                'events[0][eventid]': l2s_event.md_id,
                'events[0][repeat]': 1
            }
            self.__default_params["wsfunction"] = self.__delete_calendar_event_func
            sr_resp = requests.post(self.__req_endpoint, params=self.__default_params, data=rm_data,
                                    timeout=self.__req_timeout).json()
            if sr_resp is None or (type(sr_resp) == dict and constants.RESPONSE_ERROR_KEY not in sr_resp and
                                   constants.RESPONSE_EXCEPTION_KEY not in sr_resp):
                del_resp["response"] = sr_resp
                del_resp["err_status"] = False
            else:
                del_resp["response"] = constants.MDL_CALENDAR_EVENT_DEL_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Calendar Event Delete Exception: " + str(ex))
            del_resp["response"] = constants.MDL_CALENDAR_EVENT_DEL_EXCEPT
        return del_resp

    def check_event(self, s2l_event=None, l2s_event=None, serv_id=None):
        chk_resp = {'err_status': True, 'response': None}
        try:
            if s2l_event:
                chk_exist_object = self.__self_env[constants.CALENDAR_EVENT_MODEL].search([
                    ('md_id', '=', s2l_event['id'])
                ])
                if len(chk_exist_object) == 0:
                    filter_params = []
                    if 'course_id' in s2l_event and s2l_event['course_id']:
                        filter_params.append('&')
                        filter_params.append(('slide_id', '=', s2l_event['course_id']))
                    filter_params.append(('name', '=', s2l_event['name']))
                    chk_exist_object = self.__self_env[constants.CALENDAR_EVENT_MODEL].search(filter_params)

                if len(chk_exist_object) > 0:
                    chk_resp['response'] = chk_exist_object[0]
                    chk_resp['err_status'] = False
                else:
                    chk_resp['response'] = constants.MDL_CALENDAR_EVENT_CHK_ERR

            elif l2s_event or serv_id:
                sr_id = l2s_event.md_id if l2s_event and l2s_event.md_id else serv_id
                if sr_id:
                    filter_data = {'eventid': sr_id}
                    self.__default_params["wsfunction"] = self.__get_by_id_calendar_event_func
                    sr_resp = requests.post(self.__req_endpoint, params=self.__default_params, data=filter_data,
                                            timeout=self.__req_timeout).json()
                    if constants.RESPONSE_ERROR_KEY not in sr_resp and constants.RESPONSE_EXCEPTION_KEY not in sr_resp\
                            and 'events' in sr_resp and len(sr_resp['events']) > 0:
                        chk_resp["response"] = sr_resp['events'][0]
                        chk_resp["err_status"] = False

                if chk_resp['err_status'] and l2s_event:
                    self.__default_params["wsfunction"] = self.__get_all_calendar_events_func
                    sr_resp = requests.post(
                        self.__req_endpoint, params=self.__default_params, timeout=self.__req_timeout).json()

                    if constants.RESPONSE_ERROR_KEY not in sr_resp and constants.RESPONSE_EXCEPTION_KEY not in sr_resp\
                            and 'events' in sr_resp and len(sr_resp['events']) > 0:
                        for sr_event in sr_resp['events']:
                            if sr_event['name'] == l2s_event.name:
                                chk_resp["response"] = sr_event
                                chk_resp["err_status"] = False
                                break

                if chk_resp['err_status']:
                    chk_resp['response'] = constants.MDL_CALENDAR_EVENT_CHK_ERR

            else:
                chk_resp['response'] = constants.MDL_CALENDAR_EVENT_CHK_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Check Event Exception: " + str(ex))
            chk_resp['response'] = constants.MDL_CALENDAR_EVENT_CHK_EXCEPT
        return chk_resp

    def create_update_local_event(self, sr_event, previous_event=None):
        crt_resp = {"err_status": True, "response": None}
        try:
            start_date = datetime.fromtimestamp(sr_event['timestart'])
            duration = sr_event['timeduration'] / 3600
            end_date = datetime.fromtimestamp(sr_event['timestart']) + timedelta(minutes=60 * duration)

            data_params = {
                'name': sr_event['name'],
                'description': sr_event['description'],
                'start': start_date,
                'stop': end_date,
                'duration': duration,
                'md_id': sr_event['id']
            }
            if 'course_id' in sr_event and sr_event['course_id']:
                data_params['slide_id'] = sr_event['course_id']

            if previous_event:
                previous_event.write(data_params, addons=data_params)
                crt_resp['response'] = previous_event
                self.__js_response['updated'] += 1
            else:
                crt_resp['response'] = self.__self_env[constants.CALENDAR_EVENT_MODEL].create(data_params)
                self.__js_response['success'] += 1

            crt_resp['err_status'] = False
        except Exception as ex:
            self.__logging.exception("Moodle Calendar Event Create/Update Local Exception: " + str(ex))
            crt_resp['response'] = constants.MDL_CALENDAR_EVENT_CRT_EXCEPT
        return crt_resp

    def create_update_server_event(self, db_event, is_update=False, addon=None):
        crt_resp = {"err_status": True, "response": None}
        try:
            if not is_update and not addon:
                sr_data = {
                    "events[0][name]": db_event.name,
                    "events[0][description]": db_event.description if db_event.description else '',
                    "events[0][timestart]": int(db_event.start.timestamp()),
                    "events[0][timeduration]": int(db_event.duration * 3600) if db_event.duration else 3600
                }

                sr_course_id = db_event.slide_id.md_id
                if not sr_course_id:
                    crt_course_resp = self.__course_object.create_course(l2s_course=db_event.slide_id)
                    if not crt_course_resp['err_status']:
                        sr_course_id = crt_course_resp['response']['id']

                if sr_course_id:
                    sr_data['events[0][courseid]'] = sr_course_id
                self.__default_params["wsfunction"] = self.__create_calendar_event_func
                sr_resp = requests.post(self.__req_endpoint, params=self.__default_params, data=sr_data,
                                        timeout=self.__req_timeout).json()

                if constants.RESPONSE_ERROR_KEY not in sr_resp and constants.RESPONSE_EXCEPTION_KEY not in sr_resp\
                        and 'events' in sr_resp and len(sr_resp['events']):
                    db_event.write(
                        {'md_id': sr_resp['events'][0]['id']},
                        addons={'md_id': sr_resp['events'][0]['id']}
                    )
                    crt_resp["response"] = sr_resp['events'][0]
                    crt_resp["err_status"] = False

            if crt_resp["err_status"]:
                crt_resp["response"] = constants.MDL_CALENDAR_EVENT_CRT_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Calendar Event Create/Update Server Exception: " + str(ex))
            crt_resp['response'] = constants.MDL_CALENDAR_EVENT_CRT_EXCEPT
        return crt_resp

    def create_event(self, s2l_event=None, l2s_event=None):
        crt_tmp_resp = {"err_status": True, "response": None}
        try:
            if s2l_event:
                previous_event = None
                chk_resp = self.check_event(s2l_event=s2l_event)
                if not chk_resp['err_status']:
                    previous_event = chk_resp['response']
                crt_resp = self.create_update_local_event(sr_event=s2l_event, previous_event=previous_event)
                if not crt_resp['err_status']:
                    crt_tmp_resp['err_status'] = False
                crt_tmp_resp['response'] = crt_resp['response']

            elif l2s_event:
                is_update, addon = False, None
                chk_resp = self.check_event(l2s_event=l2s_event)
                if not chk_resp['err_status']:
                    is_update = True
                    addon = chk_resp['response']

                crt_resp = self.create_update_server_event(db_event=l2s_event, is_update=is_update, addon=addon)
                if not crt_resp['err_status']:
                    crt_tmp_resp['err_status'] = False
                crt_tmp_resp['response'] = crt_resp['response']

            else:
                crt_tmp_resp['response'] = constants.MDL_CALENDAR_EVENT_CRT_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Calendar Event Create Local/Server Exception: " + str(ex))
            crt_tmp_resp['response'] = constants.MDL_CALENDAR_EVENT_CRT_EXCEPT
        return crt_tmp_resp

    def read_serv_events(self):
        try:
            self.__default_params["wsfunction"] = self.__get_all_calendar_events_func
            sr_resp = requests.post(
                self.__req_endpoint, params=self.__default_params, timeout=self.__req_timeout).json()
            if constants.RESPONSE_ERROR_KEY not in sr_resp and constants.RESPONSE_EXCEPTION_KEY not in sr_resp \
                    and 'events' in sr_resp and len(sr_resp['events']) > 0:
                self.__js_response["total"] = len(sr_resp['events'])
                self.__js_response["response"] = sr_resp['events']
                self.__js_response["err_status"] = False
            else:
                self.__js_response["response"] = constants.MDL_CALENDAR_EVENT_WEB_SERV_IMPORT_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Calendar Event Read Server Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_CALENDAR_EVENT_WEB_SERV_IMPORT_EXCEPT

    def import_events(self):
        self.reset_response()
        try:
            self.read_serv_events()
            if not self.__js_response["err_status"]:
                for sr_event in self.__js_response["response"]:
                    crt_db_resp = self.create_event(s2l_event=sr_event)
                    if crt_db_resp["err_status"]:
                        self.__js_response["failed"] += 1
                        self.__logging.error(
                            "Moodle Calendar Event Create/Update Local Error: " + crt_db_resp['response'])
        except Exception as ex:
            self.__logging.exception("Moodle Calendar Event Import Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_CALENDAR_EVENT_WEB_IMPORT_EXCEPT
        return self.__js_response

    def write_serv_events(self, db_events):
        try:
            for db_event in db_events:
                crt_serv_resp = self.create_event(l2s_event=db_event)
                if crt_serv_resp["err_status"]:
                    self.__js_response["failed"] += 1
                    self.__logging.error(
                        "Moodle Calendar Event Create/Update Server Error: " + crt_serv_resp['response'])
        except Exception as ex:
            self.__logging.exception("Moodle Calendar Event Server Export Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_CALENDAR_EVENT_WEB_SERV_EXPORT_EXCEPT

    def export_events(self):
        self.reset_response()
        try:
            filter_query = []
            if self.__initial_date and self.__end_date:
                filter_query.append('&')
                filter_query.append('&')
                filter_query.append(('write_date', '>=', str(self.__initial_date)))
                filter_query.append(('write_date', '<=', str(self.__end_date)))

            filter_query.append(('course_id', '!=', False))
            db_events = self.__self_env[constants.CALENDAR_EVENT_MODEL].search(filter_query)
            if db_events and len(db_events) > 0:
                self.write_serv_events(db_events=db_events)
                self.__js_response["total"] = len(db_events)
                self.__js_response["err_status"] = False
            else:
                self.__js_response["response"] = constants.MDL_CALENDAR_EVENT_WEB_EXPORT_NOT_FND
        except Exception as ex:
            self.__logging.exception("Moodle Calendar Event Export Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_CALENDAR_EVENT_WEB_EXPORT_EXCEPT
        return self.__js_response
