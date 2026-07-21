from odoo import _, models
from odoo.exceptions import AccessError


class AppGradebookStudent(models.Model):
    _inherit = "app.gradebook.student"

    def _check_moodle_sync_access(self):
        authorized = self.env.user.has_group(
            "openeducat_core.group_op_faculty"
        ) or self.env.user.has_group("isep_gradebook.isep_gradebook_admin")
        if not authorized:
            raise AccessError(
                _(
                    "No tiene permisos para sincronizar notas Moodle con "
                    "la libreta."
                )
            )
        return True

    def action_open_moodle_sync_wizard(self):
        self.ensure_one()
        self._check_moodle_sync_access()
        wizard = self.env["irg.gradebook.moodle.sync.wizard"].create(
            {"gradebook_student_id": self.id}
        )
        wizard.action_load_moodle_data()
        return {
            "type": "ir.actions.act_window",
            "name": _("Sincronizar con Moodle"),
            "res_model": "irg.gradebook.moodle.sync.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }
