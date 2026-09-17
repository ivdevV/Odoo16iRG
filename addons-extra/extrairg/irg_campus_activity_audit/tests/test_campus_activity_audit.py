# -*- coding: utf-8 -*-
import base64
import io
import uuid
import zipfile
import xml.etree.ElementTree as ET

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged

from odoo.addons.irg_campus_activity_audit.wizard.listado_parser import (
    extract_course_code,
    parse_listado_xlsx,
)
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

    def _course_label(self, course=None):
        course = course or self.course
        return "%s (%s)" % (course.name, course.code)

    def _listado_xlsx(self, rows):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {"in_memory": True})
        sheet = workbook.add_worksheet("Hoja1")
        sheet.write(0, 0, "Correo electrónico")
        sheet.write(0, 1, "Curso")
        sheet.write(0, 2, "Nombre")
        sheet.write(0, 3, "País")
        sheet.write(0, 5, "modalidad")
        for index, row in enumerate(rows, start=1):
            email, course = row[0], row[1]
            name = row[2] if len(row) > 2 else ""
            country = row[3] if len(row) > 3 else ""
            modality = row[4] if len(row) > 4 else ""
            sheet.write(index, 0, email)
            sheet.write(index, 1, course)
            sheet.write(index, 2, name)
            sheet.write(index, 3, country)
            sheet.write(index, 4, "ODOO ULTIMO")
            sheet.write(index, 5, modality)
        workbook.close()
        return base64.b64encode(output.getvalue())

    def _wizard(self, **vals):
        values = {
            "listado_filename": "listado diplomados.xlsx",
        }
        if "listado_file" not in vals:
            values["listado_file"] = self._listado_xlsx([
                (
                    self.partner.email,
                    self._course_label(),
                    self.student.name,
                    "México",
                    "Modalidad semipresencial",
                ),
            ])
        values.update(vals)
        return self.env["irg.campus.activity.audit.wizard"].create(values)

    def _summary_by_email(self, wizard):
        listado = wizard._listado_rows()
        matched, unmatched = wizard._match_enrollments(listado)
        sheets = wizard._build_sheets(matched, unmatched)
        headers, rows = sheets["Resumen alumnos"]
        mapping = {row[0]: dict(zip(headers, row)) for row in rows}
        return mapping, sheets, unmatched

    def test_plain_user_cannot_generate(self):
        wizard = self._wizard()
        with self.assertRaises(AccessError):
            wizard.with_user(self.plain_user).action_generate()

    def test_missing_listado_raises(self):
        wizard = self._wizard(listado_file=False)
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_listado_without_emails_raises(self):
        wizard = self._wizard(listado_file=self._listado_xlsx([]))
        with self.assertRaises(UserError):
            wizard.action_generate()

    def test_menu_opens_wizard(self):
        menu = self.env.ref("irg_campus_activity_audit.menu_irg_campus_activity_audit")
        self.assertTrue(menu.action)
        self.assertEqual(menu.action.res_model, "irg.campus.activity.audit.wizard")

    def test_batch_form_has_no_audit_button(self):
        xmlid = "irg_campus_activity_audit.view_op_batch_form_campus_activity_audit"
        with self.assertRaises(ValueError):
            self.env.ref(xmlid)

    def test_only_listado_students_in_summary(self):
        other_partner = self.env["res.partner"].create({
            "name": "Otro Alumno Auditoria",
            "email": "otro.audit.%s@example.com" % uuid.uuid4().hex[:6],
        })
        other_vals = {
            "first_name": "Otro",
            "last_name": "Alumno",
            "partner_id": other_partner.id,
        }
        if "gender" in self.env["op.student"]._fields:
            other_vals["gender"] = "m"
        other_student = self.env["op.student"].create(other_vals)
        self.env["op.student.course"].create({
            "student_id": other_student.id,
            "course_id": self.course.id,
            "batch_id": self.batch.id,
            "state": "running",
        })
        mapping, _sheets, unmatched = self._summary_by_email(self._wizard())
        self.assertIn(self.partner.email, mapping)
        self.assertNotIn(other_partner.email, mapping)
        self.assertFalse(unmatched)

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
            (self.partner.email, self._course_label(), self.student.name, "México", "semipresencial"),
            ("nadie.audit@example.com", self._course_label(), "Nadie", "España", "semipresencial"),
        ]))
        mapping, sheets, unmatched = self._summary_by_email(wizard)
        self.assertIn(self.partner.email, mapping)
        self.assertEqual(len(unmatched), 1)
        self.assertEqual(unmatched[0]["email_norm"], "nadie.audit@example.com")
        self.assertEqual(sheets["No encontrados"][1][0][0], "nadie.audit@example.com")

    def test_wrong_course_on_listado_is_unmatched(self):
        wizard = self._wizard(listado_file=self._listado_xlsx([
            (self.partner.email, "Otro diplomado (OTRO9999)", self.student.name, "México", ""),
        ]))
        mapping, _sheets, unmatched = self._summary_by_email(wizard)
        self.assertFalse(mapping)
        self.assertEqual(len(unmatched), 1)
        self.assertIn("curso", unmatched[0].get("reason", "").lower())

    def test_parse_diplomados_listado_headers(self):
        payload = base64.b64decode(self._listado_xlsx([
            (
                "Ana@Example.com",
                "Diplomado en Evaluación (DITGHC2606)",
                "Ana Ejemplo",
                "México",
                "Modalidad semipresencial",
            ),
        ]))
        rows = parse_listado_xlsx(payload)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["email_norm"], "ana@example.com")
        self.assertEqual(rows[0]["course_code"], "DITGHC2606")
        self.assertIn("Diplomado en Evaluación", rows[0]["course_label"])
        self.assertEqual(rows[0]["name"], "Ana Ejemplo")
        self.assertEqual(rows[0]["country"], "México")
        self.assertEqual(rows[0]["modality"], "Modalidad semipresencial")

    def test_extract_course_code_from_parentheses(self):
        self.assertEqual(
            extract_course_code(
                "Diplomado en Evaluación e Intervención desde las Terapias de Tercera Generación (DITGHC2606)"
            ),
            "DITGHC2606",
        )
        self.assertEqual(extract_course_code("CAUD123"), "CAUD123")
        self.assertEqual(extract_course_code(""), "")

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
