from odoo import models, fields, api
from . import category_service
from . import constants
from . import utils
import logging


class MoodleCourseCategory(models.Model):
    _name = constants.MOODLE_CATEGORIES_MODEL
    _description = constants.MOODLE_CATEGORIES_MODEL_DESC

    name = fields.Char(string="Name", required=True)
    description = fields.Text(string="Description")
    parent_id = fields.Many2one(constants.MOODLE_CATEGORIES_MODEL, string="Parent")
    md_id = fields.Integer(string="Moodle-ID", readonly=True)

    def write(self, values, addons=None):
        _logging = logging.getLogger(__name__)

        res = super(MoodleCourseCategory, self).write(values)
        if addons is None:
            credentials = utils.get_moodle_credentials(self_env=self.env)
            if credentials:
                category_obj = category_service.MoodleCategoryService(credentials=credentials, self_env=self.env)
                for rec in self:
                    crt_resp = category_obj.create_category(l2s_category=rec)
                    if crt_resp['err_status']:
                        _logging.error("Moodle Category Create/Update Error: " + crt_resp['response'])
        return res

    @api.model
    def unlink(self, values=None):
        _logging = logging.getLogger(__name__)

        if values:
            credentials = utils.get_moodle_credentials(self_env=self.env)
            for categ_id in values:
                category_id = self.env[constants.MOODLE_CATEGORIES_MODEL].search([('id', '=', categ_id)])
                if category_id.md_id and credentials:
                    category_obj = category_service.MoodleCategoryService(credentials=credentials, self_env=self.env)
                    del_resp = category_obj.delete_category(l2s_category=category_id)
                    if del_resp['err_status']:
                        _logging.error("Moodle Category Delete Error: " + del_resp['response'])

                category_id.unlink()
        return super(MoodleCourseCategory, self).unlink()
