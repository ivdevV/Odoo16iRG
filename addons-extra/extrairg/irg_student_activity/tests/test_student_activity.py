# -*- coding: utf-8 -*-
import re

from odoo.exceptions import AccessError
from odoo.tests import tagged, TransactionCase


@tagged("post_install", "-at_install", "irg_student_activity")
class TestStudentActivity(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.faculty_group = cls.env.ref("openeducat_core.group_op_faculty")
        cls.faculty_user = cls.env["res.users"].create({
            "name": "Faculty Activity",
            "login": "faculty_activity_%s" % cls.env.cr.dbname,
            "groups_id": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.faculty_group.id,
            ])],
        })
        cls.plain_user = cls.env["res.users"].create({
            "name": "Plain Activity",
            "login": "plain_activity_%s" % cls.env.cr.dbname,
            "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
        })
        partner = cls.env["res.partner"].create({
            "name": "Alumno Activity",
            "email": "alumno.activity@example.com",
        })
        vals = {
            "name": "Alumno Activity",
            "first_name": "Alumno",
            "last_name": "Activity",
            "birth_date": "1995-01-01",
            "email": partner.email,
            "partner_id": partner.id,
        }
        if "gender" in cls.env["op.student"]._fields:
            vals["gender"] = "m"
        cls.student = cls.env["op.student"].create(vals)
        cls.partner = partner

    def test_plain_user_cannot_view_activity(self):
        student = self.student.with_user(self.plain_user)
        with self.assertRaises(AccessError):
            student._assert_can_view_activity()

    def test_empty_partner_activity_is_empty_list(self):
        rows = self.student.with_user(self.faculty_user)._activity_event_rows()
        self.assertEqual(rows, [])

    def _create_channel(self, name):
        vals = {
            "name": name,
            "channel_type": "training",
            "is_published": True,
        }
        Channel = self.env["slide.channel"]
        if "category_id" in Channel._fields and "moodle.categories" in self.env:
            category = self.env["moodle.categories"].search([], limit=1)
            if not category:
                category = self.env["moodle.categories"].create({"name": "Cat Activity"})
            vals["category_id"] = category.id
        return Channel.create(vals)

    def _create_slide(self, channel, name, **extra):
        vals = {
            "name": name,
            "channel_id": channel.id,
            "slide_category": "article",
            "is_published": True,
        }
        if "html_content" in self.env["slide.slide"]._fields:
            vals["html_content"] = "<p>ok</p>"
        vals.update(extra)
        return self.env["slide.slide"].create(vals)

    def test_campus_completed_appears_and_skips_not_started(self):
        channel = self._create_channel("Canal Activity")
        done_slide = self._create_slide(channel, "Hecho")
        self._create_slide(channel, "Sin empezar")
        self.env["slide.channel.partner"].create({
            "channel_id": channel.id,
            "partner_id": self.partner.id,
        })
        self.env["slide.slide.partner"].create({
            "slide_id": done_slide.id,
            "partner_id": self.partner.id,
            "completed": True,
        })
        rows = self.student.with_user(self.faculty_user)._activity_event_rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["event_type"], "campus")
        self.assertEqual(rows[0]["element_name"], "Hecho")
        self.assertEqual(rows[0]["detail"], "Completada")
        self.assertEqual(rows[0]["result"], "Completada")
        self.assertEqual(rows[0]["channel_name"], channel.name)

    def test_evaluation_row_and_order_with_campus(self):
        channel = self._create_channel("Canal Eval")
        survey = self.env["survey.survey"].create({"title": "Survey Activity"})
        slide = self._create_slide(
            channel,
            "Quiz slide",
            slide_category="certification",
            survey_id=survey.id,
        )
        self.env["slide.channel.partner"].create({
            "channel_id": channel.id,
            "partner_id": self.partner.id,
        })
        self.env["slide.slide.partner"].create({
            "slide_id": slide.id,
            "partner_id": self.partner.id,
            "completed": False,
        })
        Input = self.env["survey.user_input"]
        vals = {
            "survey_id": survey.id,
            "partner_id": self.partner.id,
            "state": "done",
        }
        if "slide_id" in Input._fields:
            vals["slide_id"] = slide.id
        attempt = Input.create(vals)
        if "end_datetime" in attempt._fields:
            attempt.write({"end_datetime": "2026-10-15 18:00:00"})
        sp = self.env["slide.slide.partner"].search([
            ("slide_id", "=", slide.id),
            ("partner_id", "=", self.partner.id),
        ], limit=1)
        self.env.cr.execute(
            "UPDATE slide_slide_partner SET write_date = %s, create_date = %s WHERE id = %s",
            ("2026-10-01 10:00:00", "2026-10-01 10:00:00", sp.id),
        )
        if "end_datetime" in attempt._fields:
            self.env.cr.execute(
                "UPDATE survey_user_input SET end_datetime = %s WHERE id = %s",
                ("2026-10-15 18:00:00", attempt.id),
            )
        sp.invalidate_recordset(["write_date", "create_date"])
        attempt.invalidate_recordset(["end_datetime", "create_date"])
        rows = self.student.with_user(self.faculty_user)._activity_event_rows()
        self.assertGreaterEqual(len(rows), 2)
        self.assertEqual(rows[0]["event_type"], "evaluation")
        self.assertEqual(rows[0]["element_name"], slide.name)

    def test_activity_limit_500(self):
        from datetime import datetime

        from odoo.addons.irg_student_activity.models import activity_assemble as mod

        fake = [{
            "event_datetime": datetime(2026, 1, 1),
            "event_type": "campus",
            "channel_name": "C",
            "element_name": "E%s" % i,
            "detail": "Completada",
            "result": "Completada",
            "batch_code": "",
        } for i in range(505)]
        original = mod._campus_rows
        mod._campus_rows = lambda env, partner, cache=None: fake
        try:
            rows = mod.assemble_student_activity_rows(self.env, self.student, limit=500)
        finally:
            mod._campus_rows = original
        self.assertEqual(len(rows), 500)

    def test_compute_activity_line_ids_populated(self):
        channel = self._create_channel("Canal UI")
        slide = self._create_slide(channel, "UI slide")
        self.env["slide.slide.partner"].create({
            "slide_id": slide.id,
            "partner_id": self.partner.id,
            "completed": True,
        })
        student = self.student.with_user(self.faculty_user)
        student._compute_activity_line_ids()
        self.assertEqual(len(student.activity_line_ids), 1)
        self.assertEqual(student.activity_line_ids.element_name, "UI slide")

    def test_activity_line_ids_survive_client_read(self):
        channel = self._create_channel("Canal Read")
        slide = self._create_slide(channel, "Read slide")
        self.env["slide.slide.partner"].create({
            "slide_id": slide.id,
            "partner_id": self.partner.id,
            "completed": True,
        })
        student = self.student.with_user(self.faculty_user)
        student.invalidate_recordset()
        data = student.read(["activity_line_ids"])[0]
        self.assertTrue(data["activity_line_ids"])
        lines = self.env["irg.student.activity.line"].browse(
            data["activity_line_ids"]
        )
        self.assertEqual(lines.mapped("element_name"), ["Read slide"])
        # re-reading must not accumulate lines for the same student
        student.invalidate_recordset()
        student.read(["activity_line_ids"])
        self.assertEqual(
            self.env["irg.student.activity.line"].search_count(
                [("student_id", "=", self.student.id)]
            ),
            1,
        )

    def test_export_csv_uses_user_timezone_and_no_res_link(self):
        from datetime import datetime

        from odoo import fields
        from odoo.addons.irg_student_activity.models import activity_assemble as mod
        from odoo.addons.irg_student_activity.models.csv_export import (
            build_activity_csv,
        )

        self.faculty_user.tz = "Asia/Tokyo"
        student = self.student.with_user(self.faculty_user)
        row = {
            "event_datetime": datetime(2026, 10, 15, 18, 0, 0),
            "event_type": "campus",
            "channel_name": "C",
            "element_name": "E",
            "detail": "Completada",
            "result": "",
            "batch_code": "",
        }
        text = build_activity_csv([row], student).decode("utf-8-sig")
        lines = text.splitlines()
        self.assertEqual(lines[0], ",".join(mod.CSV_HEADERS))
        self.assertTrue(lines[1].startswith("2026-10-16 03:00:00,"), lines[1])
        self.assertEqual(
            fields.Datetime.context_timestamp(student, row["event_datetime"])
            .strftime("%Y-%m-%d %H:%M:%S"),
            "2026-10-16 03:00:00",
        )

        action = student.action_export_activity_csv()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "irg.student.activity.export.wizard")
        wiz = self.env["irg.student.activity.export.wizard"].browse(action["res_id"])
        self.assertTrue(wiz.file_data)
        self.assertTrue((wiz.filename or "").endswith(".csv"))

    def test_export_csv_headers_and_row(self):
        channel = self._create_channel("Canal CSV")
        slide = self._create_slide(channel, "CSV slide")
        self.env["slide.slide.partner"].create({
            "slide_id": slide.id,
            "partner_id": self.partner.id,
            "completed": True,
        })
        action = self.student.with_user(self.faculty_user).action_export_activity_csv()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["target"], "new")
        wiz = self.env["irg.student.activity.export.wizard"].browse(action["res_id"])
        raw = __import__("base64").b64decode(wiz.file_data)
        text = raw.decode("utf-8-sig")
        self.assertTrue(text.startswith("Fecha,Tipo,"))
        self.assertIn("CSV slide", text)
        self.assertTrue((wiz.filename or "").startswith("actividad_"))

    def test_export_denied_without_faculty(self):
        with self.assertRaises(AccessError):
            self.student.with_user(self.plain_user).action_export_activity_csv()

    def test_export_csv_opens_wizard_with_binary(self):
        student = self.student.with_user(self.faculty_user)
        action1 = student.action_export_activity_csv()
        action2 = student.action_export_activity_csv()
        self.assertEqual(action1["res_model"], "irg.student.activity.export.wizard")
        self.assertEqual(action2["res_model"], "irg.student.activity.export.wizard")
        self.assertNotEqual(action1["res_id"], action2["res_id"])
        wiz = self.env["irg.student.activity.export.wizard"].browse(action2["res_id"])
        self.assertTrue(wiz.file_data)
        self.assertEqual(wiz.student_id, self.student)
