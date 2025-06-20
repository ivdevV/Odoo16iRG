from . import category_service
from . import user_service
from . import constants
from datetime import *
import requests
import logging
import time
import re


class MoodleCourseService:
    def __init__(self, credentials, self_env, initial_date=None, end_date=None):
        self.__logging = logging.getLogger(__name__)

        self.__credentials = credentials
        self.__self_env = self_env
        self.__initial_date = initial_date
        self.__end_date = end_date

        self.__category_object = category_service.MoodleCategoryService(
            credentials=credentials, self_env=self_env, initial_date=initial_date, end_date=end_date)
        self.__user_object = user_service.MoodleUserService(
            credentials=credentials, self_env=self_env, initial_date=initial_date, end_date=end_date)

        self.__req_timeout = constants.REQ_TIMEOUT
        self.__req_endpoint = constants.BASE_WEBSERVICE_URL.format(self.__credentials['base_url'])

        self.__get_courses_func = constants.MDL_COURSE_GET_ALL_FUNC
        self.__create_course_func = constants.MDL_COURSE_CREATE_FUNC
        self.__update_course_func = constants.MDL_COURSE_UPDATE_FUNC
        self.__delete_course_func = constants.MDL_COURSE_DELETE_FUNC
        self.__search_course_func = constants.MDL_COURSE_SEARCH_FUNC
        self.__enrol_course_course_func = constants.MDL_USER_ENROL_FUNC
        self.__unenrol_course_course_func = constants.MDL_USER_UNENROL_FUNC

        self.__clean_tags_re = re.compile('<.*?>')
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

    def enrol_user_to_course(self, course_id, user_id, role_id):
        en_resp = {'err_status': True, 'response': None}
        try:
            rm_data = {
                'enrolments[0][roleid]': int(role_id),
                'enrolments[0][userid]': user_id,
                'enrolments[0][courseid]': course_id
            }
            self.__default_params["wsfunction"] = self.__enrol_course_course_func
            sr_resp = requests.post(self.__req_endpoint, params=self.__default_params, data=rm_data,
                                    timeout=self.__req_timeout).json()
            if sr_resp is None or (constants.RESPONSE_ERROR_KEY not in sr_resp and
                                   constants.RESPONSE_EXCEPTION_KEY not in sr_resp):
                en_resp["response"] = sr_resp
                en_resp["err_status"] = False
            else:
                en_resp["response"] = constants.MDL_USER_ENROL_BY_COURSE_ERR
        except Exception as ex:
            self.__logging.exception("Enrolled User by Course Exception: " + str(ex))
            en_resp['response'] = constants.MDL_USER_ENROL_BY_COURSE_EXCEPT
        return en_resp

    def unenrol_user_to_course(self, course_id, user_id, role_id):
        uen_resp = {'err_status': True, 'response': None}
        try:
            rm_data = {
                'enrolments[0][roleid]': int(role_id),
                'enrolments[0][userid]': user_id,
                'enrolments[0][courseid]': course_id
            }
            self.__default_params["wsfunction"] = self.__unenrol_course_course_func
            sr_resp = requests.post(self.__req_endpoint, params=self.__default_params, data=rm_data,
                                    timeout=self.__req_timeout).json()
            if sr_resp is None or (constants.RESPONSE_ERROR_KEY not in sr_resp and
                                   constants.RESPONSE_EXCEPTION_KEY not in sr_resp):
                uen_resp["response"] = sr_resp
                uen_resp["err_status"] = False
            else:
                uen_resp["response"] = constants.MDL_USER_UNENROL_BY_COURSE_ERR
        except Exception as ex:
            self.__logging.exception("Un-Enrolled User by Course Exception: " + str(ex))
            uen_resp['response'] = constants.MDL_USER_UNENROL_BY_COURSE_EXCEPT
        return uen_resp

    def delete_course(self, l2s_course):
        del_resp = {"err_status": True, "response": None}
        try:
            rm_data = {'courseids[0]': l2s_course.md_id}
            self.__default_params["wsfunction"] = self.__delete_course_func
            sr_resp = requests.post(self.__req_endpoint, params=self.__default_params, data=rm_data,
                                    timeout=self.__req_timeout).json()
            if sr_resp is None or (constants.RESPONSE_ERROR_KEY not in sr_resp and constants.RESPONSE_EXCEPTION_KEY not in sr_resp):
                del_resp["response"] = sr_resp
                del_resp["err_status"] = False
            else:
                del_resp["response"] = constants.MDL_COURSE_DEL_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Course Delete Exception: " + str(ex))
            del_resp["response"] = constants.MDL_COURSE_DEL_EXCEPT
        return del_resp

    def check_course(self, s2l_course=None, l2s_course=None, serv_id=None):
        chk_resp = {"err_status": True, "response": None}
        try:
            if s2l_course:
                chk_object_exist = self.__self_env[constants.SLIDE_CHANNEL_MODEL].search([
                    ('md_id', '=', s2l_course['id'])
                ])
                if len(chk_object_exist) == 0:
                    chk_object_exist = self.__self_env[constants.SLIDE_CHANNEL_MODEL].search([
                        ('name', '=', s2l_course['fullname'])
                    ])
                if chk_object_exist and len(chk_object_exist) > 0:
                    chk_resp["response"] = chk_object_exist[0]
                    chk_resp["err_status"] = False
                else:
                    chk_resp["response"] = constants.MDL_COURSE_CHK_ERR

            elif l2s_course or serv_id:
                md_id = l2s_course.md_id if l2s_course and l2s_course.md_id else serv_id
                if md_id:
                    filter_data = {'options[ids][0]': md_id}
                    self.__default_params["wsfunction"] = self.__get_courses_func
                    sr_resp = requests.post(self.__req_endpoint, params=self.__default_params, data=filter_data,
                                            timeout=self.__req_timeout).json()
                    if constants.RESPONSE_ERROR_KEY not in sr_resp and \
                            constants.RESPONSE_EXCEPTION_KEY not in sr_resp and 'courses' in sr_resp and \
                            len(sr_resp['courses']) > 0:
                        chk_resp["response"] = sr_resp['courses'][0]
                        chk_resp["err_status"] = False

                if chk_resp['err_status'] and l2s_course:
                    filter_data = {
                        'criterianame': 'search',
                        'criteriavalue': l2s_course.name,
                    }
                    self.__default_params["wsfunction"] = self.__search_course_func
                    sr_resp = requests.post(self.__req_endpoint, params=self.__default_params, data=filter_data,
                                            timeout=self.__req_timeout).json()
                    if constants.RESPONSE_ERROR_KEY not in sr_resp and \
                            constants.RESPONSE_EXCEPTION_KEY not in sr_resp and 'courses' in sr_resp and \
                            len(sr_resp['courses']) > 0:
                        chk_resp["response"] = sr_resp['courses'][0]
                        chk_resp["err_status"] = False

                if chk_resp['err_status']:
                    chk_resp["response"] = constants.MDL_COURSE_CHK_ERR

            else:
                chk_resp["response"] = constants.MDL_COURSE_CHK_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Course Check Exception: " + str(ex))
            chk_resp["response"] = constants.MDL_COURSE_CHK_EXCEPT
        return chk_resp

    def create_update_local_course(self, sr_course, previous_course=None):
        crt_resp = {"err_status": True, "response": None}
        try:
            db_params = {
                'md_id': sr_course['id'],
                'name': sr_course['fullname'],
                'short_name': sr_course['shortname'],
                'description': sr_course['summary'],
                'cs_format': sr_course['format'],
                'show_grades': True if sr_course['showgrades'] else False,
                'news_items': True if sr_course['newsitems'] else 0,
                'start_date': str(datetime.fromtimestamp(sr_course['startdate'])),
                'end_date': str(datetime.fromtimestamp(sr_course['enddate'])),
                'show_reports': True if sr_course['showreports'] else False,
                'is_visible': True if sr_course['visible'] else False,
                'enable_completion': True if sr_course['enablecompletion'] else False,
                'completion_notify': True if sr_course['completionnotify'] else False,
            }

            # Check Category for Course
            gt_resp = self.__category_object.check_category(l2s_id=sr_course['categoryid'])
            if not gt_resp["err_status"]:
                crt_resp = self.__category_object.create_category(s2l_category=gt_resp["response"])
                if not crt_resp["err_status"] and type(crt_resp["response"]) != str:
                    db_params['category_id'] = crt_resp["response"].id

            # Check Language for Course
            if 'lang' in sr_course and sr_course['lang']:
                chk_lang_exist = self.__self_env[constants.RES_LANG_MODEL].search([('name', '=', sr_course['lang'])])
                if chk_lang_exist and len(chk_lang_exist) > 0:
                    db_params['lang_id'] = chk_lang_exist[0].id
                else:
                    db_params['lang_id'] = self.__self_env[constants.RES_LANG_MODEL].create({
                        'name': sr_course['lang']
                    }).id

            # Add Attendee Users to Course
            tmp_attendee_ids = []
            gt_partner_resp = self.__user_object.get_users_by_course(course_id=sr_course['id'])
            if not gt_partner_resp['err_status']:
                for sr_user in gt_partner_resp['response']:
                    crt_user_resp = self.__user_object.create_user(s2l_user=sr_user)
                    if not crt_user_resp['err_status']:
                        if crt_user_resp['response'].id not in tmp_attendee_ids:
                            tmp_attendee_ids.append(crt_user_resp['response'].id)

            if len(tmp_attendee_ids) > 0:
                db_params['channel_partner_ids'] = [(6, 0, tmp_attendee_ids)]

            if 'category_id' in db_params and db_params['category_id']:
                if previous_course:
                    previous_course.write(db_params, addons=db_params)
                    crt_resp['response'] = previous_course
                    self.__js_response['updated'] += 1
                else:
                    crt_resp['response'] = self.__self_env[constants.SLIDE_CHANNEL_MODEL].create(db_params)
                    self.__js_response['success'] += 1

                # if len(tmp_attendee_ids) > 0:
                #     self.__self_env[constants.SLIDE_CHANNEL_PARTNER_MODEL].search([
                #         ('channel_id', '=', crt_resp['response'].id)
                #     ]).unlink()

                #     for partner_id in tmp_attendee_ids:
                #         self.__self_env[constants.SLIDE_CHANNEL_PARTNER_MODEL].create({
                #             'channel_id': crt_resp['response'].id,
                #             'partner_id': partner_id
                #         })

                crt_resp['err_status'] = False
            else:
                crt_resp["response"] = constants.MDL_COURSE_CRT_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Course Create/Update Local Exception: " + str(ex))
            crt_resp["response"] = constants.MDL_COURSE_CRT_EXCEPT
        return crt_resp

    def create_update_server_course(self, db_course, is_update=False, addon=None):
        crt_resp = {"err_status": True, "response": None}
        try:
            sr_categ_id = None
            if not db_course.category_id.md_id:
                crt_categ_serv = self.__category_object.create_category(l2s_category=db_course.category_id)
                if not crt_categ_serv["err_status"]:
                    sr_categ_id = crt_categ_serv["response"][0]["id"]
                    db_course.category_id.write({'md_id': sr_categ_id}, addons={'md_id': sr_categ_id})
            else:
                sr_categ_id = db_course.category_id.md_id

            if sr_categ_id:
                prm_data = {
                    'courses[0][fullname]': db_course.name,
                    'courses[0][categoryid]': sr_categ_id,
                    'courses[0][summaryformat]': 1,
                    'courses[0][format]': db_course.cs_format,
                    'courses[0][showgrades]': 1 if db_course.show_grades else 0,
                    'courses[0][newsitems]': 1 if db_course.news_items else 0,
                    'courses[0][showreports]': 1 if db_course.show_reports else 0,
                    'courses[0][visible]': 1 if db_course.is_visible else 0,
                    'courses[0][enablecompletion]': 1 if db_course.enable_completion else 0,
                    'courses[0][completionnotify]': 1 if db_course.completion_notify else 0,
                }

                if db_course.short_name:
                    prm_data['courses[0][shortname]'] = db_course.short_name
                if db_course.description:
                    prm_data['courses[0][summary]'] = re.sub(self.__clean_tags_re, '', db_course.description)
                if db_course.start_date:
                    prm_data['courses[0][startdate]'] = int(time.mktime(db_course.start_date.timetuple()))
                if db_course.end_date:
                    prm_data['courses[0][enddate]'] = int(time.mktime(db_course.end_date.timetuple()))
                # if db_course.lang_id:
                #     prm_data['courses[0][lang]'] = db_course.lang_id.url_code

                if is_update and addon:
                    sr_id = db_course.md_id if db_course.md_id else addon['id']
                    prm_data['courses[0][id]'] = sr_id
                    self.__default_params["wsfunction"] = self.__update_course_func

                    sr_resp = requests.post(
                        self.__req_endpoint, params=self.__default_params, data=prm_data,
                        timeout=self.__req_timeout).json()
                    if constants.RESPONSE_ERROR_KEY in sr_resp or \
                            constants.RESPONSE_EXCEPTION_KEY in sr_resp or len(sr_resp) == 0:
                        prm_data['courses[0][id]'] = addon['id']
                        self.__default_params["wsfunction"] = self.__update_course_func
                else:
                    self.__default_params["wsfunction"] = self.__create_course_func

                sr_resp = requests.post(
                    self.__req_endpoint, params=self.__default_params, data=prm_data, timeout=self.__req_timeout).json()
                if constants.RESPONSE_ERROR_KEY not in sr_resp and \
                        constants.RESPONSE_EXCEPTION_KEY not in sr_resp and len(sr_resp) > 0:
                    if is_update:
                        self.__js_response['updated'] += 1
                    else:
                        self.__js_response['success'] += 1

                    if type(sr_resp) == list:
                        db_course.write({"md_id": sr_resp[0]['id']}, addons={"md_id": sr_resp[0]['id']})
                        crt_resp["response"] = sr_resp[0]
                    else:
                        sr_course_obj = None
                        if 'courses' in sr_resp:
                            sr_course_obj = sr_resp['courses'][0]
                        elif 'course' in sr_resp:
                            sr_course_obj = sr_resp['course'][0]

                        if sr_course_obj:
                            db_course.write(
                                {"md_id": sr_course_obj['id']},
                                addons={"md_id": sr_course_obj['id']}
                            )
                            crt_resp["response"] = sr_course_obj

                    crt_resp["err_status"] = False
                else:
                    crt_resp["response"] = constants.MDL_COURSE_CRT_ERR
            else:
                crt_resp["response"] = constants.MDL_COURSE_CRT_ERR

            if not crt_resp['err_status'] and len(db_course.channel_partner_ids) > 0:
                sr_course_id = db_course.md_id if db_course.md_id else crt_resp['response']['íd']
                if sr_course_id and type(sr_course_id) != str:
                    previous_course_users = self.__user_object.get_users_by_course(course_id=sr_course_id)
                    if not previous_course_users['err_status']:
                        for sr_course_user in previous_course_users['response']:
                            if 'roles' in sr_course_user:
                                for role_id in sr_course_user['roles']:
                                    tmp_unrol_resp = self.unenrol_user_to_course(
                                        course_id=sr_course_id, user_id=sr_course_user['id'], role_id=role_id['roleid'])

                    for db_partner in db_course.channel_partner_ids:
                        sr_user_id = None
                        if db_partner.partner_id.md_id:
                            sr_user_id = db_partner.partner_id.md_id
                        else:
                            crt_user_resp = self.__user_object.create_user(l2s_user=db_partner.partner_id)
                            if not crt_user_resp['err_status']:
                                sr_user_id = crt_user_resp['response']['id']

                        if sr_user_id:
                            tmp_enrol_resp = self.enrol_user_to_course(
                                course_id=sr_course_id, user_id=sr_user_id, role_id=db_partner.role)
        except Exception as ex:
            self.__logging.exception("Moodle Course Create/Update Server Exception: " + str(ex))
            crt_resp["response"] = constants.MDL_COURSE_CRT_EXCEPT
        return crt_resp

    def create_course(self, s2l_course=None, l2s_course=None):
        crt_tmp_resp = {"err_status": True, "response": None}
        try:
            if s2l_course:
                previous_course = None
                chk_resp = self.check_course(s2l_course=s2l_course)
                if not chk_resp['err_status']:
                    previous_course = chk_resp['response']
                crt_resp = self.create_update_local_course(sr_course=s2l_course, previous_course=previous_course)
                if not crt_resp['err_status']:
                    crt_tmp_resp['err_status'] = False
                crt_tmp_resp['response'] = crt_resp['response']

            elif l2s_course:
                is_update, addon = False, None
                chk_resp = self.check_course(l2s_course=l2s_course)
                if not chk_resp['err_status']:
                    is_update = True
                    addon = chk_resp['response']
                crt_resp = self.create_update_server_course(db_course=l2s_course, is_update=is_update, addon=addon)
                if not crt_resp['err_status']:
                    crt_tmp_resp['err_status'] = False
                crt_tmp_resp['response'] = crt_resp['response']
            else:
                crt_tmp_resp["response"] = constants.MDL_COURSE_CRT_ERR
        except Exception as ex:
            self.__logging.exception("Create User Exception: " + str(ex))
            crt_tmp_resp["response"] = constants.MDL_COURSE_CRT_EXCEPT
        return crt_tmp_resp

    def read_serv_courses(self):
        try:
            self.__default_params["wsfunction"] = self.__get_courses_func
            sr_resp = requests.post(
                self.__req_endpoint, params=self.__default_params, timeout=self.__req_timeout).json()
            if constants.RESPONSE_ERROR_KEY and len(sr_resp) > 0:
                self.__js_response["total"] = len(sr_resp)
                self.__js_response["response"] = sr_resp
                self.__js_response["err_status"] = False
            else:
                self.__js_response["response"] = constants.MDL_COURSE_WEB_SERV_IMPORT_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Courses Import Server Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_COURSE_WEB_SERV_IMPORT_EXCEPT

    def import_courses(self):
        self.reset_response()
        try:
            self.read_serv_courses()
            if not self.__js_response["err_status"]:
                for sr_course in self.__js_response["response"]:
                    crt_resp = self.create_course(s2l_course=sr_course)
                    if crt_resp["err_status"]:
                        self.__js_response["failed"] += 1
                        self.__logging.error("Course Create/Update Local Error:" + crt_resp["response"])
        except Exception as ex:
            self.__logging.exception("Moodle Courses Import Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_COURSE_WEB_IMPORT_EXCEPT
        return self.__js_response

    def write_serv_courses(self, _db_courses):
        try:
            for db_course in _db_courses:
                crt_resp = self.create_course(l2s_course=db_course)
                if crt_resp["err_status"]:
                    self.__js_response["failed"] += 1
                    self.__logging.error("Course Create/Update Server Error:" + crt_resp["response"])
        except Exception as ex:
            self.__logging.exception("Moodle Courses Export Server Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_COURSE_WEB_SERV_EXPORT_EXCEPT

    def export_courses(self):
        self.reset_response()
        try:
            filter_query = []
            if self.__initial_date and self.__end_date:
                filter_query.append('&')
                filter_query.append(('create_date', '>=', str(self.__initial_date)))
                filter_query.append(('create_date', '<=', str(self.__end_date)))

            db_course_courses = self.__self_env[constants.SLIDE_CHANNEL_MODEL].search(filter_query)
            if db_course_courses and len(db_course_courses) > 0:
                self.write_serv_courses(_db_courses=db_course_courses)
                self.__js_response["total"] = len(db_course_courses)
                self.__js_response["err_status"] = False
            else:
                self.__js_response["response"] = constants.MDL_COURSE_WEB_EXPORT_NOT_FND
        except Exception as ex:
            self.__logging.exception("Moodle Courses Export Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_COURSE_WEB_EXPORT_EXCEPT
        return self.__js_response
