from odoo import api, fields, models


class AppGradebookResult(models.Model):
    _inherit = "app.gradebook.result"

    is_moodle = fields.Boolean(
        string="Origen Moodle",
        default=False,
        index=True,
        help="Línea creada/actualizada por el wizard de sincronización Moodle.",
    )
    moodle_sync_key = fields.Char(
        string="Clave sincronización Moodle",
        compute="_compute_moodle_sync_key",
        store=True,
        index=True,
        copy=False,
    )

    _sql_constraints = [
        (
            "moodle_sync_key_uniq",
            "unique(moodle_sync_key)",
            "Ya existe una nota Moodle para esta asignatura y tipo.",
        )
    ]

    @api.depends("is_moodle", "gradebook_subject_id", "survey_type")
    def _compute_moodle_sync_key(self):
        for result in self:
            if (
                result.is_moodle
                and result.gradebook_subject_id
                and result.survey_type
            ):
                result.moodle_sync_key = "%s:%s" % (
                    result.gradebook_subject_id.id,
                    result.survey_type,
                )
            else:
                result.moodle_sync_key = False
