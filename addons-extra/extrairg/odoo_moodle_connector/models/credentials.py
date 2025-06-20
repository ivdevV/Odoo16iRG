from odoo import models, fields
from . import constants
import logging


class MoodleCredentials(models.Model):
    _name = constants.MOODLE_CREDENTIALS_MODEL
    _description = constants.MOODLE_CREDENTIALS_MODEL_DESC

    access_token = fields.Char(string="Access Token", required=True, default=lambda self: self._get_default_token())
    request_url = fields.Char(string="Request URL", required=True, default=lambda self: self._get_default_req_url())

    def _get_default_token(self):
        latest_record = self.env[constants.MOODLE_CREDENTIALS_MODEL].search([])
        return latest_record[constants.INITIAL_INDEX].access_token if len(latest_record) > 0 else ''

    def _get_default_req_url(self):
        latest_record = self.env[constants.MOODLE_CREDENTIALS_MODEL].search([])
        return latest_record[constants.INITIAL_INDEX].request_url if len(latest_record) > 0 else ''

    def get_default_credentials(self):
        credentials = {}
        latest_record = self.env[constants.MOODLE_CREDENTIALS_MODEL].search([])
        if len(latest_record) > 0:
            credentials['access_token'] = latest_record[constants.INITIAL_INDEX].access_token
            credentials['base_url'] = latest_record[constants.INITIAL_INDEX].request_url
        else:
            credentials[constants.RESPONSE_ERROR_KEY] = True
            credentials[constants.RESPONSE_ERR_MESSAGE_KEY] = constants.MDL_CREDENTIALS_NOT_FND
        return credentials

    def connect(self):
        _logging = logging.getLogger(__name__)

        rep_message = ''
        val_struct = {
            'access_token': self.access_token,
            'request_url': self.request_url
        }
        try:
            db_rows = self.env[self._name].search([])
            if db_rows and len(db_rows) > 0:
                _logging.info("Moodle Credentials Update CRD record")
                db_rows[constants.INITIAL_INDEX].write(val_struct)
            else:
                _logging.info("Moodle Credentials Create CRD record")
                super().create(val_struct)
            rep_message += constants.MDL_CREDENTIALS_CNT_SUC
        except Exception as ex:
            _logging.exception("Moodle Credentials Connect Exception: " + str(ex))
            rep_message += constants.MDL_CREDENTIALS_CNT_EXCEPT
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "System Notification",
                'message': rep_message,
                'sticky': False,
            }
        }
