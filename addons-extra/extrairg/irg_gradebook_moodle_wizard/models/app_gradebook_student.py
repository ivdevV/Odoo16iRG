from odoo import _, models


class AppGradebookStudent(models.Model):
    _inherit = "app.gradebook.student"

    def action_open_moodle_sync_wizard(self):
        self.ensure_one()
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
