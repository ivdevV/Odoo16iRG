from odoo import models, fields
from . import constants


class MoodleExportStats(models.Model):
    _name = constants.MOODLE_EXPORT_STATS_MODEL
    _description = constants.MOODLE_EXPORT_STATS_MODEL_DESC

    connector = fields.Many2one(constants.MOODLE_CONNECTOR_MODEL, string="Reference")
    new_user = fields.Integer(string="New User")
    new_category = fields.Integer(string="New Category")
    new_course = fields.Integer(string="New Course")
    new_event = fields.Integer(string="New Event")

    upd_user = fields.Integer(string="Update User")
    upd_category = fields.Integer(string="Update Category")
    upd_course = fields.Integer(string="Update Course")
