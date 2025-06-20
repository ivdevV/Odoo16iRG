from . import constants
import requests
import logging
import base64
import re


class MoodleUserService:
    def __init__(self, credentials, self_env, initial_date=None, end_date=None):
        self.__logging = logging.getLogger(__name__)

        self.__credentials = credentials
        self.__self_env = self_env
        self.__initial_date = initial_date
        self.__end_date = end_date

        self.__req_timeout = constants.REQ_TIMEOUT
        self.__req_endpoint = constants.BASE_WEBSERVICE_URL.format(self.__credentials['base_url'])

        self.__get_users_func = constants.MDL_USER_GET_ALL_FUNC
        self.__create_user_func = constants.MDL_USER_CREATE_FUNC
        self.__update_user_func = constants.MDL_USER_UPDATE_FUNC
        self.__delete_user_func = constants.MDL_USER_DELETE_FUNC
        self.__enrol_course_user_func = constants.MDL_USER_ENROL_FUNC
        self.__unenrol_course_user_func = constants.MDL_USER_UNENROL_FUNC
        self.__enrol_users_by_course_func = constants.MDL_USER_GET_USERS_BY_COURSE_FUNC

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

    def get_users_by_course(self, course_id):
        gt_resp = {"err_status": True, "response": None}
        try:
            req_data = {'courseid': course_id}
            self.__default_params["wsfunction"] = self.__enrol_users_by_course_func
            sr_resp = requests.post(
                self.__req_endpoint, params=self.__default_params, data=req_data, timeout=self.__req_timeout).json()
            if constants.RESPONSE_ERROR_KEY not in sr_resp and constants.RESPONSE_EXCEPTION_KEY not in sr_resp:
                gt_resp['response'] = sr_resp
                gt_resp['err_status'] = False
            else:
                gt_resp['response'] = constants.MDL_USER_GET_ALL_BY_COURSE_ERR
        except Exception as ex:
            self.__logging.exception("Get Users from Course Exception: " + str(ex))
            gt_resp['response'] = constants.MDL_USER_GET_ALL_BY_COURSE_EXCEPT
        return gt_resp

    def delete_user(self, l2s_user):
        del_resp = {"err_status": True, "response": None}
        try:
            rm_data = {
                'users[0][id]': l2s_user.md_id,
                'users[0][recursive]': 0
            }
            self.__default_params["wsfunction"] = self.__delete_user_func
            sr_resp = requests.post(
                self.__req_endpoint, params=self.__default_params, data=rm_data, timeout=self.__req_timeout).json()
            if sr_resp is None or (constants.RESPONSE_ERROR_KEY not in sr_resp and
                                   constants.RESPONSE_EXCEPTION_KEY not in sr_resp):
                del_resp["response"] = sr_resp
                del_resp["err_status"] = False
            else:
                del_resp["response"] = constants.MDL_USER_DEL_ERR
        except Exception as ex:
            self.__logging.exception("Moodle User Delete User Exception: " + str(ex))
            del_resp["response"] = constants.MDL_USER_DEL_EXCEPT
        return del_resp

    def check_user(self, s2l_user=None, l2s_user=None, serv_id=None):
        chk_resp = {"err_status": True, "response": None}
        try:
            if s2l_user:
                chk_object_exist = self.__self_env[constants.RES_PARTNER_MODEL].search([
                    ('md_id', '=', s2l_user['id'])
                ])
                if len(chk_object_exist) == 0:
                    chk_object_exist = self.__self_env[constants.RES_PARTNER_MODEL].search([
                        ('email', '=', s2l_user['email'])
                    ])

                if chk_object_exist and len(chk_object_exist) > 0:
                    chk_resp["response"] = chk_object_exist[0]
                    chk_resp["err_status"] = False
                else:
                    chk_resp["response"] = constants.MDL_USER_CHK_ERR

            elif l2s_user or serv_id:
                sr_id = l2s_user.md_id if l2s_user and l2s_user.md_id else serv_id
                if sr_id:
                    filter_data = {
                        'criteria[0][key]': 'id',
                        'criteria[0][value]': sr_id
                    }
                    self.__default_params["wsfunction"] = self.__get_users_func
                    sr_resp = requests.post(self.__req_endpoint, params=self.__default_params, data=filter_data,
                                            timeout=self.__req_timeout).json()
                    if constants.RESPONSE_ERROR_KEY not in sr_resp and 'users' in sr_resp and len(sr_resp['users']) > 0:
                        chk_resp["response"] = sr_resp['users'][0]
                        chk_resp["err_status"] = False

                if chk_resp['err_status'] and l2s_user:
                    filter_data = {
                        'criteria[0][key]': 'email',
                        'criteria[0][value]': l2s_user.email
                    }
                    self.__default_params["wsfunction"] = self.__get_users_func
                    sr_resp = requests.post(self.__req_endpoint, params=self.__default_params, data=filter_data,
                                            timeout=self.__req_timeout).json()
                    if constants.RESPONSE_ERROR_KEY not in sr_resp and 'users' in sr_resp and len(sr_resp['users']) > 0:
                        chk_resp["response"] = sr_resp['users'][0]
                        chk_resp["err_status"] = False

                if chk_resp['err_status']:
                    chk_resp["response"] = constants.MDL_USER_CHK_ERR

            else:
                chk_resp["response"] = constants.MDL_USER_CHK_ERR
        except Exception as ex:
            self.__logging.exception("Moodle User Check Exception: " + str(ex))
            chk_resp["response"] = constants.MDL_USER_CHK_EXCEPT
        return chk_resp

    def create_update_local_user(self, sr_user, previous_user=None):
        crt_resp = {"err_status": True, "response": None}
        try:
            inst_id, dept_id = None, None

            thumbnail = base64.b64encode(requests.get(sr_user['profileimageurl']).content)
            full_name = sr_user['firstname']
            if 'middlename' in sr_user and sr_user['middlename']:
                full_name += " {0}".format(sr_user['middlename'])
            if 'lastname' in sr_user and sr_user['lastname']:
                full_name += " {0}".format(sr_user['lastname'])

            db_data = {
                'md_id': sr_user["id"],
                'username': sr_user['username'],
                'email': sr_user['email'],
                'name': full_name,
                'image_1920': thumbnail,
            }

            if 'address' in sr_user and sr_user['address']:
                db_data['street'] = sr_user['address']
            if 'city' in sr_user and sr_user['city']:
                db_data['city'] = sr_user['city']
            if 'description' in sr_user and sr_user['description']:
                db_data['comment'] = sr_user['description']
            if 'phone1' in sr_user and sr_user['phone1']:
                db_data['phone'] = sr_user['phone1']
            if 'phone2' in sr_user and sr_user['phone2']:
                db_data['mobile'] = sr_user['phone2']

            if 'suspended' in sr_user:
                db_data['is_suspended'] = sr_user['suspended']
            if 'confirmed' in sr_user:
                db_data['is_confirmed'] = sr_user['confirmed']
            if 'country' in sr_user and sr_user['country']:
                chk_country_exist = self.__self_env[constants.RES_COUNTRY_MODEL].search([
                    ('code', '=', sr_user['country'])
                ])
                if len(chk_country_exist) == 0:
                    chk_country_exist = self.__self_env[constants.RES_COUNTRY_MODEL].create({
                        'name': sr_user['country'],
                        'code': sr_user['country']
                    })
                if len(chk_country_exist) > 0:
                    db_data['country_id'] = chk_country_exist[0].id

            # Institution Addition
            if 'institution' in sr_user and sr_user['institution']:
                chk_exist_inst = self.__self_env[constants.RES_PARTNER_MODEL].search([
                    ('name', '=', sr_user['institution'])
                ])
                if chk_exist_inst and len(chk_exist_inst) > 0:
                    inst_id = chk_exist_inst[0].id
                else:
                    inst_id = self.__self_env[constants.RES_PARTNER_MODEL].create({
                        'name': sr_user['institution'],
                        'is_company': True,
                    }).id

            if inst_id:
                db_data["institution"] = inst_id

            # Department Addition
            if 'department' in sr_user and sr_user['department']:
                chk_exist_dept = self.__self_env[constants.HR_DEPARTMENT_MODEL].search([
                    ('name', '=', sr_user['department'])
                ])
                if chk_exist_dept and len(chk_exist_dept) > 0:
                    dept_id = chk_exist_dept[0].id
                else:
                    dept_id = self.__self_env[constants.HR_DEPARTMENT_MODEL].create({
                        'name': sr_user['department']
                    }).id
            if dept_id:
                db_data["department"] = dept_id

            if 'customfields' in sr_user and sr_user['customfields']:
                for _cs_field in sr_user["customfields"]:
                    if _cs_field["type"] == "birthday":
                        db_data['birth_date'] = _cs_field["value"]
                    elif _cs_field["type"] == "blood_group":
                        db_data['blood_group'] = _cs_field["value"]
                    elif _cs_field["type"] == "gender":
                        db_data['gender'] = _cs_field["value"]
                    elif _cs_field["type"] == "state":
                        chk_state_exist = self.__self_env[constants.RES_COUNTRY_STATE_MODEL].search([
                            ('name', '=', _cs_field["value"])
                        ])
                        if chk_state_exist and len(chk_state_exist) > 0:
                            db_data['state_id'] = chk_state_exist[0].id
                        else:
                            db_data['state_id'] = self.__self_env[constants.RES_COUNTRY_STATE_MODEL].create({
                                'name': _cs_field["value"]
                            }).id

            if 'interests' in sr_user and len(sr_user['interests']) > 0:
                tmp_interest_ids = []
                for value in sr_user['interests'].split(','):
                    chk_inter_exist = self.__self_env[constants.RES_PARTNER_CATEGORY_MODEL].search([
                        ('name', '=', value)
                    ])
                    if chk_inter_exist and len(chk_inter_exist) > 0:
                        rel_id = chk_inter_exist[0].id
                    else:
                        rel_id = self.__self_env[constants.RES_PARTNER_CATEGORY_MODEL].create({'name': value}).id

                    if rel_id not in tmp_interest_ids:
                        tmp_interest_ids.append(rel_id)

                if len(tmp_interest_ids) > 0:
                    db_data['category_id'] = [(6, 0, tmp_interest_ids)]

            if previous_user:
                previous_user.write(db_data, addons=db_data)
                crt_resp["response"] = previous_user
                self.__js_response['updated'] += 1
            else:
                crt_resp["response"] = self.__self_env[constants.RES_PARTNER_MODEL].create(db_data)
                self.__js_response['success'] += 1

            crt_resp["err_status"] = False
        except Exception as ex:
            self.__logging.exception("Moodle User Create/Update Local Exception: " + str(ex))
            crt_resp["response"] = constants.MDL_USER_CRT_EXCEPT
        return crt_resp

    def create_update_server_user(self, db_user, is_update=False, addon=None):
        crt_resp = {"err_status": True, "response": None}
        try:
            idx = 0
            full_name = db_user.name.split(' ')
            prm_data = {
                'users[0][username]': db_user.username.lower().replace(' ', ''),
                'users[0][auth]': 'manual',
                'users[0][firstname]': full_name[0],
                'users[0][email]': db_user.email,
            }
            if len(full_name) > 1:
                prm_data['users[0][lastname]'] = ' '.join(full_name[1:])
            else:
                prm_data['users[0][lastname]'] = full_name[0]

            prm_data['users[0][firstnamephonetic]'] = prm_data['users[0][firstname]']
            prm_data['users[0][lastnamephonetic]'] = prm_data['users[0][lastname]']
            prm_data['users[0][alternatename]'] = db_user.name

            if db_user.street:
                prm_data['users[0][address]'] = db_user.street
            if db_user.city:
                prm_data['users[0][city]'] = db_user.city
            if db_user.country_id:
                prm_data['users[0][country]'] = db_user.country_id.code
            if db_user.comment:
                prm_data['users[0][description]'] = re.sub(self.__clean_tags_re, '', db_user.comment)

            if db_user.institution:
                prm_data['users[0][institution]'] = db_user.institution.name
            if db_user.department:
                prm_data['users[0][department]'] = db_user.department.name

            if db_user.phone:
                prm_data['users[0][phone1]'] = db_user.phone
            if db_user.mobile:
                prm_data['users[0][phone2]'] = db_user.mobile

            if not is_update:
                if db_user.password:
                    prm_data['users[0][password]'] = db_user.password
                else:
                    prm_data['users[0][createpassword]'] = 1

            if db_user.category_id and len(db_user.category_id) > 0:
                tmp_interest_list = ''
                for _interest in db_user.category_id:
                    tmp_interest_list += _interest.name + ','
                prm_data['users[0][interests]'] = tmp_interest_list[:-1]

            if db_user.birth_date:
                prm_data['users[0][customfields][' + str(idx) + '][type]'] = 'birthday'
                prm_data['users[0][customfields][' + str(idx) + '][value]'] = str(db_user.birth_date)
                idx += 1

            if db_user.blood_group:
                prm_data['users[0][customfields][' + str(idx) + '][type]'] = 'blood_group'
                prm_data['users[0][customfields][' + str(idx) + '][value]'] = str(db_user.blood_group)
                idx += 1

            if db_user.gender:
                prm_data['users[0][customfields][' + str(idx) + '][type]'] = 'gender'
                prm_data['users[0][customfields][' + str(idx) + '][value]'] = str(db_user.gender)
                idx += 1

            if db_user.state_id:
                prm_data['users[0][customfields][3][type]'] = 'state'
                prm_data['users[0][customfields][3][value]'] = str(db_user.state_id.name)

            if is_update and addon:
                srv_id = db_user.md_id if db_user.md_id else addon['id']
                prm_data['users[0][id]'] = srv_id
                self.__default_params["wsfunction"] = self.__update_user_func

                sr_resp = requests.post(
                    self.__req_endpoint, params=self.__default_params, data=prm_data,
                    timeout=self.__req_timeout).json()
                if constants.RESPONSE_ERROR_KEY in sr_resp or \
                        constants.RESPONSE_EXCEPTION_KEY in sr_resp or len(sr_resp) == 0:
                    prm_data['users[0][id]'] = addon['id']
                    self.__default_params["wsfunction"] = self.__update_user_func
            else:
                self.__default_params["wsfunction"] = self.__create_user_func

            sr_resp = requests.post(
                self.__req_endpoint, params=self.__default_params, data=prm_data, timeout=self.__req_timeout).json()

            if constants.RESPONSE_ERROR_KEY not in sr_resp and \
                    constants.RESPONSE_EXCEPTION_KEY not in sr_resp and len(sr_resp) > 0:
                if is_update and addon:
                    self.__js_response['updated'] += 1
                else:
                    self.__js_response['success'] += 1

            if not is_update:
                if sr_resp and constants.RESPONSE_ERROR_KEY not in sr_resp and \
                        constants.RESPONSE_EXCEPTION_KEY not in sr_resp and len(sr_resp) > 0:

                    srv_id = sr_resp[0]['id']
                    db_user.write({"md_id": srv_id}, addons={"md_id": srv_id})
                    crt_resp["response"] = db_user
                    crt_resp["err_status"] = False
                else:
                    crt_resp["response"] = constants.MDL_USER_CRT_ERR
            elif sr_resp is None:
                crt_resp["response"] = db_user
                crt_resp["err_status"] = False
            else:
                crt_resp["response"] = constants.MDL_USER_CRT_ERR

            # if not crt_resp["err_status"] and srv_id and db_user.image_1920:
            #     img_resp = self.upload_image(db_user=db_user, sr_id=srv_id)
            #     if not img_resp["err_status"]:
            #         assoc_resp = self.associate_user_image(sr_id=srv_id, img_info=img_resp["response"])
            #         if assoc_resp["err_status"]:
            #             self.__logging.error("Image Associate with Person Error: " + assoc_resp["response"])
            #     else:
            #         self.__logging.error("Person Image Upload Error: " + img_resp["response"])

        except Exception as ex:
            self.__logging.exception("Moodle User Create/Update Server Exception: " + str(ex))
            crt_resp["response"] = constants.MDL_USER_CRT_EXCEPT
        return crt_resp

    def create_user(self, s2l_user=None, l2s_user=None):
        crt_tmp_resp = {"err_status": True, "response": None}
        try:
            if s2l_user:
                previous_user = None
                chk_resp = self.check_user(s2l_user=s2l_user)
                if not chk_resp['err_status']:
                    previous_user = chk_resp['response']
                crt_resp = self.create_update_local_user(sr_user=s2l_user, previous_user=previous_user)
                if not crt_resp['err_status']:
                    crt_tmp_resp['err_status'] = False
                crt_tmp_resp["response"] = crt_resp["response"]

            elif l2s_user:
                is_update, addon = False, None
                chk_resp = self.check_user(l2s_user=l2s_user)
                if not chk_resp['err_status']:
                    is_update = True
                    addon = chk_resp['response']
                crt_resp = self.create_update_server_user(db_user=l2s_user, is_update=is_update, addon=addon)
                if not crt_resp["err_status"]:
                    crt_tmp_resp["err_status"] = False
                crt_tmp_resp["response"] = crt_resp["response"]

            else:
                crt_tmp_resp["response"] = constants.MDL_USER_CRT_ERR
        except Exception as ex:
            self.__logging.exception("Moodle User Create/Update Local/Server Exception: " + str(ex))
            crt_tmp_resp["response"] = constants.MDL_USER_CRT_EXCEPT
        return crt_tmp_resp

    def read_serv_users(self):
        try:
            self.__default_params["wsfunction"] = self.__get_users_func
            req_data = {
                "criteria[0][key]": "lastname",
                "criteria[0][value]": "%"
            }
            sr_resp = requests.post(
                self.__req_endpoint, params=self.__default_params, data=req_data, timeout=self.__req_timeout).json()
            if constants.RESPONSE_ERROR_KEY not in sr_resp and constants.RESPONSE_EXCEPTION_KEY not in sr_resp \
                    and 'users' in sr_resp and len(sr_resp['users']) > 0:
                self.__js_response["total"] = len(sr_resp['users'])
                self.__js_response["response"] = sr_resp['users']
                self.__js_response["err_status"] = False
            else:
                self.__js_response["response"] = constants.MDL_USER_WEB_SERV_IMPORT_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Users Import Server Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_USER_WEB_SERV_IMPORT_EXCEPT

    def import_users(self):
        self.reset_response()
        try:
            self.read_serv_users()
            if not self.__js_response["err_status"]:
                for sr_user in self.__js_response["response"]:
                    crt_resp = self.create_user(s2l_user=sr_user)
                    if crt_resp["err_status"]:
                        self.__js_response['failed'] += 1
                        self.__logging.error("Moodle User Create/Update Local Error: " + crt_resp["response"])
        except Exception as ex:
            self.__logging.exception("Moodle Users Import Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_USER_WEB_IMPORT_EXCEPT
        return self.__js_response

    def write_serv_users(self, _db_channel_users):
        try:
            for db_user in _db_channel_users:
                crt_resp = self.create_user(l2s_user=db_user)
                if crt_resp["err_status"]:
                    self.__js_response['failed'] += 1
                    self.__logging.error("Moodle User Create/Update Server Error: " + crt_resp["response"])
        except Exception as ex:
            self.__logging.exception("Moodle Users Export Server Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_USER_WEB_SERV_EXPORT_EXCEPT

    def export_users(self):
        self.reset_response()
        try:
            filter_query = []
            if self.__initial_date and self.__end_date:
                filter_query.append('&')
                filter_query.append(('create_date', '>=', str(self.__initial_date)))
                filter_query.append(('create_date', '<=', str(self.__end_date)))

            db_course_users = self.__self_env[constants.RES_PARTNER_MODEL].search(filter_query)
            if db_course_users and len(db_course_users) > 0:
                self.write_serv_users(_db_channel_users=db_course_users)
                self.__js_response["total"] = len(db_course_users)
                self.__js_response["err_status"] = False
            else:
                self.__js_response["response"] = constants.MDL_USER_WEB_EXPORT_NOT_FND
        except Exception as ex:
            self.__logging.exception("Moodle Users Export Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_USER_WEB_EXPORT_EXCEPT
        return self.__js_response
