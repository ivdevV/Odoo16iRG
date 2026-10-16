# -*- coding: utf-8 -*-
import base64
import re

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

from .activity_assemble import ACTIVITY_LIMIT, assemble_student_activity_rows
from .csv_export import build_activity_csv


class OpStudent(models.Model):
    _inherit = "op.student"

    activity_line_ids = fields.One2many(
        "irg.student.activity.line",
        "student_id",
        string="Actividad",
        compute="_compute_activity_line_ids",
        readonly=True,
    )

    def _assert_can_view_activity(self):
        if not self.env.su and not self.env.user.has_group(
            "openeducat_core.group_op_faculty"
        ):
            raise AccessError(
                _("Solo el personal de Facultad puede ver la actividad del alumno.")
            )

    def _activity_event_rows(self):
        self.ensure_one()
        self._assert_can_view_activity()
        return assemble_student_activity_rows(
            self.sudo().env, self.sudo(), limit=ACTIVITY_LIMIT
        )

    @api.depends("partner_id")
    def _compute_activity_line_ids(self):
        # Odoo 16 read() drops NewId records without origin, so inline
        # (0, 0, vals) commands would leave the tab empty in the web client.
        # Materialise real TransientModel rows (vacuumed automatically) and
        # link them with (6, 0, ids); previous rows of the student are removed
        # first so they do not pile up.
        Line = self.env["irg.student.activity.line"]
        for student in self:
            if not student.id:
                student.activity_line_ids = [(5, 0, 0)]
                continue
            try:
                rows = student._activity_event_rows()
            except AccessError:
                student.activity_line_ids = [(5, 0, 0)]
                continue
            Line.search([
                ("student_id", "=", student.id),
                ("create_uid", "=", self.env.user.id),
            ]).unlink()
            lines = Line.create([{
                "student_id": student.id,
                "event_datetime": row["event_datetime"],
                "event_type": row["event_type"],
                "channel_name": row["channel_name"],
                "element_name": row["element_name"],
                "detail": row["detail"],
                "result": row["result"],
                "batch_code": row["batch_code"],
            } for row in rows])
            student.activity_line_ids = [(6, 0, lines.ids)]

    def action_export_activity_csv(self):
        self.ensure_one()
        try:
            rows = self._activity_event_rows()
            payload = build_activity_csv(rows, self)
        except AccessError:
            raise
        except Exception as error:
            raise UserError(
                _("No se pudo generar el CSV de actividad: %s") % error
            ) from error
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", (self.name or "alumno").strip())[:40]
        filename = "actividad_%s_%s.csv" % (
            slug or "alumno",
            fields.Date.context_today(self).strftime("%Y%m%d"),
        )
        # Transient wizard with Binary field: same pattern as campus audit /
        # admission export. Visible in the UI for download (act_url downloads
        # are invisible to browser E2E harnesses).
        wizard = self.env["irg.student.activity.export.wizard"].create({
            "student_id": self.id,
            "file_data": base64.b64encode(payload),
            "filename": filename,
            "state": "done",
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Exportar actividad CSV"),
            "res_model": "irg.student.activity.export.wizard",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }
