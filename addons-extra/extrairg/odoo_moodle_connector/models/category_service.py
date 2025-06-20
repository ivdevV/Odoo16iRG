from . import constants
import requests
import logging


class MoodleCategoryService:
    def __init__(self, credentials, self_env, initial_date=None, end_date=None):
        self.__logging = logging.getLogger(__name__)

        self.__credentials = credentials
        self.__self_env = self_env
        self.__initial_date = initial_date
        self.__end_date = end_date

        self.__service_sub_url = constants.BASE_WEBSERVICE_URL
        self.__req_endpoint = constants.BASE_WEBSERVICE_URL.format(self.__credentials['base_url'])
        self.__req_timeout = constants.REQ_TIMEOUT

        self.__get_category_func = constants.MDL_CATEGORY_GET_ALL_FUNC
        self.__create_category_func = constants.MDL_CATEGORY_CREATE_FUNC
        self.__update_category_func = constants.MDL_CATEGORY_UPDATE_FUNC
        self.__delete_category_func = constants.MDL_CATEGORY_DELETE_FUNC

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

    def delete_category(self, l2s_category):
        del_resp = {"err_status": True, "response": None}
        try:
            rm_data = {
                'categories[0][id]': l2s_category.md_id,
                'categories[0][recursive]': 0
            }
            self.__default_params["wsfunction"] = self.__delete_category_func
            sr_resp = requests.post(
                self.__req_endpoint, params=self.__default_params, data=rm_data, timeout=self.__req_timeout).json()
            if sr_resp and constants.RESPONSE_ERROR_KEY not in sr_resp or \
                    constants.RESPONSE_EXCEPTION_KEY not in sr_resp:
                del_resp["response"] = sr_resp
                del_resp["err_status"] = False
            else:
                del_resp["response"] = constants.MDL_CATEGORY_DEL_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Categories Delete Exception: " + str(ex))
            del_resp["response"] = constants.MDL_CATEGORY_DEL_EXCEPT
        return del_resp

    def check_category(self, s2l_category=None, l2s_category=None, l2s_id=None):
        chk_resp = {"err_status": True, "response": None}
        try:
            if s2l_category:
                chk_object_exist = self.__self_env[constants.MOODLE_CATEGORIES_MODEL].search([
                    ('md_id', '=', s2l_category['id'])
                ])
                if len(chk_object_exist) == 0:
                    chk_object_exist = self.__self_env[constants.MOODLE_CATEGORIES_MODEL].search([
                        ('name', '=', s2l_category['name'])
                    ])
                if chk_object_exist and len(chk_object_exist) > 0:
                    chk_resp["response"] = chk_object_exist[0]
                    chk_resp["err_status"] = False
                else:
                    chk_resp["response"] = constants.MDL_CATEGORY_CHK_ERR

            elif l2s_category or l2s_id:
                md_id = l2s_category.md_id if l2s_category and l2s_category.md_id else l2s_id
                if md_id:
                    filter_data = {
                        'criteria[0][key]': 'id',
                        'criteria[0][value]': md_id
                    }
                    self.__default_params["wsfunction"] = self.__get_category_func
                    sr_resp = requests.post(self.__req_endpoint, params=self.__default_params, data=filter_data,
                                            timeout=self.__req_timeout).json()
                    if constants.RESPONSE_ERROR_KEY not in sr_resp and constants.RESPONSE_EXCEPTION_KEY not in sr_resp\
                            and len(sr_resp) > 0:
                        for tmp_sr_categ in sr_resp:
                            if tmp_sr_categ['id'] == md_id:
                                chk_resp["response"] = tmp_sr_categ
                                break

                        if not chk_resp['response']:
                            chk_resp["response"] = sr_resp[0]
                        chk_resp["err_status"] = False

                if l2s_category and chk_resp['err_status']:
                    filter_data = {
                        'criteria[0][key]': 'name',
                        'criteria[0][value]': l2s_category.name
                    }
                    self.__default_params["wsfunction"] = self.__get_category_func
                    sr_resp = requests.post(self.__req_endpoint, params=self.__default_params, data=filter_data,
                                            timeout=self.__req_timeout).json()
                    if constants.RESPONSE_ERROR_KEY not in sr_resp and constants.RESPONSE_EXCEPTION_KEY not in sr_resp\
                            and len(sr_resp) > 0:
                        chk_resp["response"] = sr_resp[0]
                        chk_resp["err_status"] = False

                if chk_resp['err_status']:
                    chk_resp["response"] = constants.MDL_CATEGORY_CHK_ERR
            else:
                chk_resp["response"] = constants.MDL_CATEGORY_CHK_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Categories Check Exception: " + str(ex))
            chk_resp["response"] = constants.MDL_CATEGORY_CHK_EXCEPT
        return chk_resp

    def create_update_local_category(self, sr_category, previous_category=None):
        crt_resp = {"err_status": True, "response": None}
        try:
            data_params = {
                "name": sr_category["name"],
                "md_id": sr_category["id"],
            }
            if "description" in sr_category and sr_category["description"]:
                data_params["description"] = sr_category["description"]

            if 'parent' in sr_category and sr_category['parent']:
                gt_category = self.check_category(l2s_id=sr_category['parent'])
                if not gt_category['err_status']:
                    crt_tmp_resp = self.create_category(s2l_category=gt_category['response'])
                    if not crt_tmp_resp['err_status']:
                        data_params['parent_id'] = crt_tmp_resp['response'].id

            if previous_category:
                previous_category.write(data_params, addons=data_params)
                crt_resp['response'] = previous_category
                self.__js_response['updated'] += 1
            else:
                crt_resp['response'] = self.__self_env[constants.MOODLE_CATEGORIES_MODEL].create(data_params)
                self.__js_response['success'] += 1

            crt_resp['err_status'] = False
        except Exception as ex:
            self.__logging.exception("Moodle Categories Create/Update Local Exception: " + str(ex))
            crt_resp["response"] = constants.MDL_CATEGORY_CRT_EXCEPT
        return crt_resp

    def create_update_server_category(self, db_category, is_update=False, addon=None):
        crt_resp = {"err_status": True, "response": None}
        try:
            serv_data = {
                'categories[0][name]': db_category.name,
            }
            if db_category.description and len(db_category.description) > 0:
                serv_data['categories[0][description]'] = db_category.description

            if db_category.parent_id:
                if db_category.parent_id.md_id:
                    serv_data["categories[0][parent]"] = db_category.parent_id.md_id
                else:
                    crt_prt_resp = self.create_category(l2s_category=db_category.parent_id)
                    if not crt_prt_resp["err_status"]:
                        serv_data["categories[0][parent]"] = crt_prt_resp["response"]['id']

            if is_update and addon:
                self.__default_params["wsfunction"] = self.__update_category_func
                serv_data['categories[0][id]'] = db_category.md_id if db_category.md_id else addon['id']
                sr_resp = requests.post(
                    self.__req_endpoint, params=self.__default_params, data=serv_data,
                    timeout=self.__req_timeout).json()

                if sr_resp and (constants.RESPONSE_ERROR_KEY in sr_resp or constants.RESPONSE_EXCEPTION_KEY in sr_resp):
                    serv_data['categories[0][id]'] = addon['id']
                    sr_resp = requests.post(
                        self.__req_endpoint, params=self.__default_params, data=serv_data,
                        timeout=self.__req_timeout).json()
            else:
                self.__default_params["wsfunction"] = self.__create_category_func
                sr_resp = requests.post(
                    self.__req_endpoint, params=self.__default_params, data=serv_data,
                    timeout=self.__req_timeout).json()

            if constants.RESPONSE_ERROR_KEY not in sr_resp and \
                    constants.RESPONSE_EXCEPTION_KEY not in sr_resp and len(sr_resp) > 0:
                if type(sr_resp) == list:
                    sr_resp = sr_resp[0]

                db_category.write({"md_id": sr_resp['id']}, addons={"md_id": sr_resp['id']})
                crt_resp["response"] = sr_resp
                crt_resp["err_status"] = False
            else:
                crt_resp["response"] = constants.MDL_CATEGORY_CRT_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Categories Create/Update Server Exception: " + str(ex))
            crt_resp["response"] = constants.MDL_CATEGORY_CRT_EXCEPT
        return crt_resp

    def create_category(self, s2l_category=None, l2s_category=None):
        crt_tmp_resp = {"err_status": True, "response": None}
        try:
            if s2l_category:
                previous_category = None
                chk_resp = self.check_category(s2l_category=s2l_category)
                if not chk_resp['err_status']:
                    previous_category = chk_resp['response']
                crt_resp = self.create_update_local_category(
                    sr_category=s2l_category, previous_category=previous_category)
                if not crt_resp['err_status']:
                    crt_tmp_resp['err_status'] = False
                crt_tmp_resp['response'] = crt_resp['response']

            elif l2s_category:
                is_update, addon = False, None
                chk_resp = self.check_category(l2s_category=l2s_category)
                if not chk_resp['err_status']:
                    addon = chk_resp['response']
                    is_update = True
                crt_resp = self.create_update_server_category(
                    db_category=l2s_category, is_update=is_update, addon=addon)
                if not crt_resp['err_status']:
                    crt_tmp_resp['err_status'] = False
                crt_tmp_resp['response'] = crt_resp['response']

            else:
                crt_tmp_resp['response'] = constants.MDL_CATEGORY_CRT_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Categories Create/Update Local Exception: " + str(ex))
            crt_tmp_resp["response"] = constants.MDL_CATEGORY_CRT_EXCEPT
        return crt_tmp_resp

    def read_serv_categories(self):
        try:
            self.__default_params["wsfunction"] = self.__get_category_func
            sr_resp = requests.post(
                self.__req_endpoint, params=self.__default_params, timeout=self.__req_timeout).json()
            if constants.RESPONSE_ERROR_KEY not in sr_resp and constants.RESPONSE_EXCEPTION_KEY not in sr_resp \
                    and len(sr_resp) > 0:
                self.__js_response["total"] = len(sr_resp)
                self.__js_response["response"] = sr_resp
                self.__js_response["err_status"] = False
            else:
                self.__js_response["response"] = constants.MDL_CATEGORY_WEB_SERV_IMPORT_ERR
        except Exception as ex:
            self.__logging.exception("Moodle Categories Import Server Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_CATEGORY_WEB_SERV_IMPORT_EXCEPT

    def import_categories(self):
        self.reset_response()
        try:
            self.read_serv_categories()
            if not self.__js_response["err_status"]:
                for sr_category in self.__js_response["response"]:
                    crt_resp = self.create_category(s2l_category=sr_category)
                    if crt_resp["err_status"]:
                        self.__js_response["failed"] += 1
                        self.__logging.info("Moodle Category Create/Update Local Error: " + crt_resp['response'])
        except Exception as ex:
            self.__logging.exception("Moodle Categories Import Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_CATEGORY_WEB_IMPORT_EXCEPT
        return self.__js_response

    def write_serv_categories(self, _db_categories):
        try:
            for db_category in _db_categories:
                crt_resp = self.create_category(l2s_category=db_category)
                if crt_resp["err_status"]:
                    self.__js_response["failed"] += 1
                    self.__logging.info("Moodle Category Create/Update Server Error: " + crt_resp['response'])
        except Exception as ex:
            self.__logging.exception("Moodle Categories Server Export Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_CATEGORY_WEB_SERV_EXPORT_EXCEPT

    def export_categories(self):
        self.reset_response()
        try:
            filter_query = []
            if self.__initial_date and self.__end_date:
                filter_query.append('&')
                filter_query.append(('create_date', '>=', str(self.__initial_date)))
                filter_query.append(('create_date', '<=', str(self.__end_date)))

            db_course_categories = self.__self_env[constants.MOODLE_CATEGORIES_MODEL].search(filter_query)
            if db_course_categories and len(db_course_categories) > 0:
                self.write_serv_categories(_db_categories=db_course_categories)
                self.__js_response["total"] = len(db_course_categories)
                self.__js_response["err_status"] = False
            else:
                self.__js_response["response"] = constants.MDL_CATEGORY_WEB_EXPORT_NOT_FND
        except Exception as ex:
            self.__logging.exception("Moodle Categories Export Exception: " + str(ex))
            self.__js_response["response"] = constants.MDL_CATEGORY_WEB_EXPORT_EXCEPT
        return self.__js_response
