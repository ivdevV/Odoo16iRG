# -*- coding: utf-8 -*-
import base64
import io
import uuid
import zipfile
import xml.etree.ElementTree as ET

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.irg_campus_activity_audit.wizard.listado_parser import parse_listado_xlsx
from odoo.addons.irg_campus_activity_audit.wizard.xlsx_export import SHEET_ORDER

try:
    import xlsxwriter
except ImportError:
    xlsxwriter = None


def _xlsx_sheet_names(payload):
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
        return [sheet.attrib.get("name") for sheet in workbook.findall("m:sheets/m:sheet", ns)]


@tagged("post_install", "-at_install", "irg_campus_activity_audit")
class TestCampusActivityAudit(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        suffix = uuid.uuid4().hex[:6].upper()
        course_vals = {
            "name": "Curso Auditoria Campus %s" % suffix,
            "code": "CAUD%s" % suffix[:8],
        }
        if "lang" in cls.env["op.course"]._fields:
            course_vals["lang"] = "en_US"
        cls.course = cls.env["op.course"].create(course_vals)
        cls.batch = cls.env["op.batch"].create({
            "name": "Lote Auditoria %s" % suffix,
            "code": "BAUD%s" % suffix[:8],
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "course_id": cls.course.id,
        })
        cls.subject = cls.env["op.subject"].create({
            "name": "Asignatura Auditoria %s" % suffix,
            "code": "SAUD%s" % suffix[:8],
            "subject_type": "compulsory",
            "course_id": cls.course.id,
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Alumno Auditoria %s" % suffix,
            "email": "alumno.audit.%s@example.com" % suffix.lower(),
        })
        student_vals = {
            "first_name": "Alumno",
            "last_name": "Auditoria %s" % suffix,
            "partner_id": cls.partner.id,
        }
        if "gender" in cls.env["op.student"]._fields:
            student_vals["gender"] = "m"
        cls.student = cls.env["op.student"].create(student_vals)
        cls.enrollment = cls.env["op.student.course"].create({
            "student_id": cls.student.id,
            "course_id": cls.course.id,
            "batch_id": cls.batch.id,
            "state": "running",
        })
        cls.faculty_user = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Facultad Auditoria %s" % suffix,
            "login": "faculty.audit.%s" % suffix.lower(),
            "email": "faculty.audit.%s@example.com" % suffix.lower(),
            "groups_id": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("openeducat_core.group_op_faculty").id,
            ])],
        })
        cls.plain_user = cls.env["res.users"].with_context(no_reset_password=True).create({
            "name": "Interno sin Facultad %s" % suffix,
            "login": "plain.audit.%s" % suffix.lower(),
            "email": "plain.audit.%s@example.com" % suffix.lower(),
            "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
        })

    def _wizard(self, **vals):
        values = {"batch_id": self.batch.id}
        values.update(vals)
        return self.env["irg.campus.activity.audit.wizard"].create(values)

    def _listado_xlsx(self, rows):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Listado")
        sheet.write(0, 0, "email")
        sheet.write(0, 1, "curso")
        for index, (email, course) in enumerate(rows, start=1):
            sheet.write(index, 0, email)
            sheet.write(index, 1, course)
        workbook.close()
        return base64.b64encode(output.getvalue())

    def _summary_by_email(self, wizard):
        enrollments = wizard._enrollments()
        matched, unmatched = wizard._match_enrollments(enrollments, wizard._listado_rows())
        sheets = wizard._build_sheets(matched, unmatched, bool(wizard.listado_file))
        headers, rows = sheets["Resumen alumnos"]
        mapping = {row[0]: dict(zip(headers, row)) for row in rows}
        return mapping, sheets, unmatched

    def test_plain_user_cannot_generate(self):
        wizard = self._wizard()
        with self.assertRaises(AccessError):
            wizard.with_user(self.plain_user).action_generate()

    def test_empty_batch_raises(self):
        self.enrollment.unlink()
        wizard = self._wizard()
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_batch_action_opens_wizard(self):
        action = self.batch.action_open_campus_activity_audit()
        self.assertEqual(action["res_model"], "irg.campus.activity.audit.wizard")
        self.assertEqual(action["context"]["default_batch_id"], self.batch.id)

    def test_enrollments_come_from_batch(self):
        wizard = self._wizard()
        enrollments = wizard._enrollments()
        self.assertEqual(enrollments, self.enrollment)

    def test_matricula_finalizada_flag(self):
        wizard = self._wizard()
        mapping, _sheets, _unmatched = self._summary_by_email(wizard)
        row = mapping[self.partner.email]
        self.assertEqual(row["matricula_finalizada"], "No")
        self.assertEqual(row["matricula_estado"], "running")
        self.enrollment.write({"state": "finished"})
        mapping, _sheets, _unmatched = self._summary_by_email(wizard)
        row = mapping[self.partner.email]
        self.assertEqual(row["matricula_finalizada"], "Sí")
        self.assertEqual(row["matricula_estado"], "finished")

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
                category = self.env["moodle.categories"].create({
                    "name": "Categoria Auditoria",
                })
            vals["category_id"] = category.id
        return Channel.create(vals)

    def test_campus_completed_when_all_slides_done(self):
        channel = self._create_channel("Canal Auditoria %s" % self.batch.code)
        slide_vals = {
            "name": "Contenido 1",
            "channel_id": channel.id,
            "slide_category": "article",
            "is_published": True,
        }
        if "html_content" in self.env["slide.slide"]._fields:
            slide_vals["html_content"] = "<p>ok</p>"
        slide = self.env["slide.slide"].create(slide_vals)
        membership_vals = {
            "channel_id": channel.id,
            "partner_id": self.partner.id,
            "batch_id": self.batch.id,
        }
        if "course_id" in self.env["slide.channel.partner"]._fields:
            membership_vals["course_id"] = self.course.id
        if "op_subject_id" in self.env["slide.channel.partner"]._fields:
            membership_vals["op_subject_id"] = self.subject.id
        self.env["slide.channel.partner"].create(membership_vals)
        wizard = self._wizard()
        mapping, sheets, _unmatched = self._summary_by_email(wizard)
        row = mapping[self.partner.email]
        self.assertEqual(row["campus_completado"], "No")
        self.assertEqual(row["actividades_publicadas"], 1)
        self.assertEqual(row["actividades_completadas"], 0)
        self.env["slide.slide.partner"].create({
            "slide_id": slide.id,
            "partner_id": self.partner.id,
            "completed": True,
        })
        mapping, sheets, _unmatched = self._summary_by_email(wizard)
        row = mapping[self.partner.email]
        self.assertEqual(row["campus_completado"], "Sí")
        activities = sheets["Actividades"][1]
        self.assertTrue(any(item[6] == "Completada" for item in activities))

    def test_libreta_100_uses_completion_porc(self):
        register_vals = {
            "name": "Registro Auditoria %s" % self.batch.code,
            "course_id": self.course.id,
            "start_date": "2026-01-01",
            "end_date": "2026-12-31",
            "min_count": 1,
            "max_count": 100,
        }
        if "product_id" in self.env["op.admission.register"]._fields:
            product = self.env["product.product"].create({
                "name": "Producto Auditoria %s" % self.batch.code,
                "type": "service",
            })
            register_vals["product_id"] = product.id
        register = self.env["op.admission.register"].create(register_vals)
        admission_vals = {
            "name": self.student.name,
            "first_name": "Alumno",
            "last_name": self.student.last_name,
            "email": self.partner.email,
            "partner_id": self.partner.id,
            "student_id": self.student.id,
            "course_id": self.course.id,
            "register_id": register.id,
            "birth_date": "1995-01-01",
        }
        if "gender" in self.env["op.admission"]._fields:
            admission_vals["gender"] = "m"
        if "batch_id" in self.env["op.admission"]._fields:
            admission_vals["batch_id"] = self.batch.id
        admission = self.env["op.admission"].create(admission_vals)
        book = self.env["app.gradebook.student"].create({
            "admission_id": admission.id,
            "state": "in_progress",
        })
        grade_subject = self.env["app.gradebook.subject"].create({
            "gradebook_student_id": book.id,
            "op_subject_id": self.subject.id,
        })
        self.env["app.gradebook.result"].create({
            "gradebook_subject_id": grade_subject.id,
            "survey_type": "exam",
            "scoring_total": 9.0,
            "description": "Examen auditoria",
        })
        self.enrollment.invalidate_recordset(["completion_porc"])
        wizard = self._wizard()
        flags = wizard._completion_flags(self.enrollment)
        self.assertGreaterEqual(flags["completion_porc"], 100.0)
        self.assertTrue(flags["libreta_100"])
        mapping, sheets, _unmatched = self._summary_by_email(wizard)
        self.assertEqual(mapping[self.partner.email]["libreta_100"], "Sí")
        self.assertTrue(sheets["Libreta examenes"][1])

    def test_listado_unmatched_goes_to_sheet(self):
        wizard = self._wizard(listado_file=self._listado_xlsx([
            (self.partner.email, self.course.code),
            ("nadie.audit@example.com", self.course.code),
        ]))
        mapping, sheets, unmatched = self._summary_by_email(wizard)
        self.assertIn(self.partner.email, mapping)
        self.assertEqual(len(unmatched), 1)
        self.assertEqual(unmatched[0]["email_norm"], "nadie.audit@example.com")
        self.assertEqual(sheets["No encontrados"][1][0][0], "nadie.audit@example.com")

    def test_parse_listado_xlsx_headers(self):
        payload = base64.b64decode(self._listado_xlsx([
            ("Ana@Example.com", "CAUD"),
        ]))
        rows = parse_listado_xlsx(payload)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["email_norm"], "ana@example.com")
        self.assertEqual(rows[0]["course_code"], "CAUD")

    def test_generate_xlsx_contains_expected_sheets(self):
        wizard = self._wizard()
        write_date = self.enrollment.write_date
        wizard.with_user(self.faculty_user).action_generate()
        self.assertEqual(wizard.state, "done")
        self.assertTrue(wizard.file_data)
        names = _xlsx_sheet_names(base64.b64decode(wizard.file_data))
        for expected in SHEET_ORDER:
            self.assertIn(expected, names)
        self.enrollment.invalidate_recordset()
        self.assertEqual(self.enrollment.write_date, write_date)
        self.assertEqual(self.enrollment.state, "running")

    def test_generate_does_not_create_enrollments(self):
        count_before = self.env["op.student.course"].search_count([])
        self._wizard().action_generate()
        self.assertEqual(
            self.env["op.student.course"].search_count([]),
            count_before,
        )
