from odoo import models, fields, api
from . import user_service
from . import constants
from . import utils
import logging


class MoodleResPartner(models.Model):
    _inherit = constants.RES_PARTNER_MODEL

    username = fields.Char(string="Username", required=True)
    md_id = fields.Integer(string="Moodle-ID", readonly=True)
    lang_id = fields.Many2one(constants.RES_LANG_MODEL, string='Language')
    institution = fields.Many2one(constants.RES_PARTNER_MODEL, string='Institution')
    department = fields.Many2one(constants.HR_DEPARTMENT_MODEL, string='Department')
    active = fields.Boolean(default=True, string="Active")
    is_suspended = fields.Boolean(default=False, string="Suspended")
    is_confirmed = fields.Boolean(default=False, string="Confirmed")

    birth_date = fields.Date(string="Birthday")
    blood_group = fields.Selection([
        ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'),
        ('O-', 'O-')], string="Blood Group", default='A+')
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female'), ('not-sure', 'Not Sure')], string="Gender", default='male')

    def write(self, values, addons=None):
        _logging = logging.getLogger(__name__)
        
        res = super(MoodleResPartner, self).write(values)
        credentials = utils.get_moodle_credentials(self_env=self.env)
        for rec in self:
            if not addons and credentials:
                user_obj = user_service.MoodleUserService(credentials=credentials, self_env=self.env)
                crt_resp = user_obj.create_user(l2s_user=rec)
                if crt_resp['err_status']:
                    _logging.error("Moodle User Create/Update Error: " + crt_resp['response'])            
        
        return res

    @api.model
    def unlink(self, values=None):
        _logging = logging.getLogger(__name__)

        if values:
            for usr_id in values:
                db_user_id = self.env[constants.RES_PARTNER_MODEL].search([('id', '=', usr_id)])
                credentials = utils.get_moodle_credentials(self_env=self.env)
                if db_user_id.md_id and credentials:
                    user_obj = user_service.MoodleUserService(credentials=credentials, self_env=self.env)
                    del_resp = user_obj.delete_user(l2s_user=db_user_id)
                    if del_resp['err_status']:
                        _logging.error("Moodle User Delete Error: " + del_resp['response'])

                db_user_id.unlink()
        return super(MoodleResPartner, self).unlink()
