from odoo import fields, models


class ForumForum(models.Model):
    _inherit = "forum.forum"

    notify_students_email = fields.Boolean(
        string="Notify Students by Email",
        default=False,
        help="If enabled, students/followers receive an email when a new publication is created in this forum.",
    )