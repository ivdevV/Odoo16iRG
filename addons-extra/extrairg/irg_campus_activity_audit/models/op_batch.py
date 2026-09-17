# -*- coding: utf-8 -*-
from odoo import _, models


class OpBatch(models.Model):
    _inherit = "op.batch"

    def action_open_campus_activity_audit(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Informe de actividad"),
            "res_model": "irg.campus.activity.audit.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_batch_id": self.id,
                "active_id": self.id,
                "active_model": "op.batch",
            },
        }
