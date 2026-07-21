from odoo import fields, models


class AppGradebookResult(models.Model):
    _inherit = "app.gradebook.result"

    is_moodle = fields.Boolean(
        string="Origen Moodle",
        default=False,
        index=True,
        help="Línea creada/actualizada por el wizard de sincronización Moodle.",
    )
