# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from lxml import etree

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged

DUMMY_SIGNATURE = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@tagged("post_install", "-at_install")
class TestPracticeAgreementSpecific(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        today = fields.Date.today()
        cls.partner = cls.env["res.partner"].create({
            "name": "Centro Colaborador Test S.L.",
            "vat": "B87654321",
            "email": "centro.especifico@example.test",
            "phone": "930009900",
        })
        cls.center = cls.env["practice.center"].create({
            "name": "Centro Colaborador Test",
            "official_name": "Centro Colaborador Test S.L.",
            "signatory_name": "Ana Representante",
            "partner_id": cls.partner.id,
            "street": "Carrer Provença 100",
            "city": "Barcelona",
            "postal_code": "08015",
            "email": "centro.especifico@example.test",
            "phone": "930009900",
        })
        course_vals = {
            "name": "Máster de Prueba iRG",
            "code": "IRG-ESP-INT",
        }
        if "lang" in cls.env["op.course"]._fields:
            course_vals["lang"] = cls.env.user.lang or "en_US"
        cls.course = cls.env["op.course"].create(course_vals)
        cls.batch = cls.env["op.batch"].create({
            "name": "Lote específico",
            "code": "IRG-ESP-B",
            "course_id": cls.course.id,
            "start_date": today,
            "end_date": today + relativedelta(months=1),
        })
        cls.student_partner = cls.env["res.partner"].create({
            "name": "Alumno Prueba Específico",
            "email": "alumno.especifico@example.test",
            "vat": "X1234567Y",
        })
        cls.student = cls.env["op.student"].create({
            "partner_id": cls.student_partner.id,
            "first_name": "Alumno",
            "last_name": "Prueba Específico",
            "gender": "o",
        })
        cls.enrollment = cls.env["op.student.course"].create({
            "student_id": cls.student.id,
            "course_id": cls.course.id,
            "batch_id": cls.batch.id,
        })
        cls.practice_type = cls.env["practice.center.type"].create({
            "type_of_practice": "on_site",
        })
        cls.tutor = cls.env["res.partner"].create({
            "name": "Tutor de Prueba",
            "vat": "12345678Z",
            "tutor": True,
            "email": "tutor.especifico@example.test",
        })
        cls.request = cls.env["practice.request"].create({
            "name": "Alumno Prueba Específico",
            "email": "alumno.especifico@example.test",
            "course_id": cls.enrollment.id,
            "practice_center_type_id": cls.practice_type.id,
            "solicited_practice_center_ids": [(6, 0, [cls.center.id])],
            "practice_center_id": cls.center.id,
            "tutor_id": cls.tutor.id,
            "start_date": today,
            "final_date": today + relativedelta(days=28),
            "total_hours": 50.0,
            "monday_available_start_time": 8.0,
            "monday_available_end_time": 12.0,
            "tuesday_available_start_time": 8.0,
            "tuesday_available_end_time": 12.0,
            "wednesday_available_start_time": 8.0,
            "wednesday_available_end_time": 12.0,
        })

    def _render_agreement_html(self, agreement):
        html, _fmt = self.env["ir.actions.report"]._render_qweb_html(
            "irg_practice_agreement_sign.action_report_practice_agreement",
            [agreement.id],
        )
        if isinstance(html, bytes):
            html = html.decode("utf-8")
        return str(html)

    def _create_especifico(self, activities="", agreement_type="especifico_internacional"):
        Wizard = self.env["irg.practice.agreement.specific.create.wizard"]
        action = Wizard.create({
            "practice_request_id": self.request.id,
            "agreement_type": agreement_type,
            "student_proposed_activities": activities,
        }).action_create_agreement()
        return self.env["practice.agreement"].browse(action["res_id"])

    def test_agreement_type_includes_especifico_internacional(self):
        field = self.env["practice.agreement"]._fields.get("agreement_type")
        self.assertIsNotNone(field)
        keys = dict(field.selection)
        self.assertIn("especifico_internacional", keys)
        self.assertIn("especifico_nacional", keys)
        self.assertIn("marco_nacional", keys)
        self.assertIn("marco_internacional", keys)

    def test_wizard_model_exists(self):
        self.assertIn(
            "irg.practice.agreement.specific.create.wizard",
            self.env.registry,
        )

    def test_request_button_opens_wizard(self):
        view_id = self.env.ref("isep_practices_2.view_practice_request_form").id
        arch = self.env["practice.request"].get_view(
            view_id=view_id, view_type="form"
        )["arch"]
        root = etree.fromstring(arch.encode() if isinstance(arch, str) else arch)
        buttons = root.xpath(
            "//button[@name='action_open_create_specific_agreement_wizard']"
        )
        self.assertTrue(
            buttons,
            "El formulario de la solicitud debe abrir el wizard de convenio específico.",
        )
        self.assertEqual(buttons[0].get("string"), "Crear Convenio")

    def test_wizard_creates_especifico_with_snapshots(self):
        agreement = self._create_especifico()
        self.assertEqual(agreement.agreement_type, "especifico_internacional")
        self.assertEqual(agreement.practice_request_id, self.request)
        self.assertEqual(agreement.practice_center_id, self.center)
        self.assertEqual(agreement.student_name, "Alumno Prueba Específico")
        self.assertEqual(agreement.student_email, "alumno.especifico@example.test")
        self.assertEqual(agreement.student_vat, "X1234567Y")
        self.assertEqual(agreement.course_name, "Máster de Prueba iRG")
        self.assertEqual(agreement.tutor_name, "Tutor de Prueba")
        self.assertEqual(agreement.total_hours, 50.0)
        self.assertIn("Lunes", agreement.practice_days or "")
        self.assertTrue(agreement.student_access_token)
        self.assertNotEqual(agreement.student_access_token, agreement.access_token)

    def test_wizard_requires_assigned_center(self):
        request = self.env["practice.request"].create({
            "name": "Alumno Sin Centro",
            "email": "sin.centro@example.test",
            "course_id": self.enrollment.id,
            "practice_center_type_id": self.practice_type.id,
        })
        Wizard = self.env["irg.practice.agreement.specific.create.wizard"]
        wizard = Wizard.create({
            "practice_request_id": request.id,
            "agreement_type": "especifico_internacional",
        })
        with self.assertRaises(UserError):
            wizard.action_create_agreement()

    def test_html_has_insurance_and_no_inmira(self):
        agreement = self._create_especifico()
        html = self._render_agreement_html(agreement)
        self.assertIn("fuera de España", html)
        self.assertIn("Anexo I", html)
        self.assertIn("no remunerad", html.lower())
        self.assertIn("Alumno Prueba Específico", html)
        self.assertIn("Centro Colaborador Test", html)
        self.assertNotIn("INMIRA", html)
        self.assertNotIn("Área de Psicología", html)
        self.assertNotIn("actividades propuestas por el alumno", html.lower())

    def test_html_shows_optional_activities(self):
        agreement = self._create_especifico(
            "Observación de sesiones clínicas bajo supervisión."
        )
        html = self._render_agreement_html(agreement)
        self.assertIn("actividades propuestas por el alumno", html.lower())
        self.assertIn("Observación de sesiones clínicas bajo supervisión.", html)
        self.assertNotIn("INMIRA", html)

    def test_student_and_center_urls_differ(self):
        agreement = self._create_especifico()
        center_url = agreement.get_portal_url()
        student_url = agreement.get_student_portal_url()
        self.assertIn("/convenio/firma/", center_url)
        self.assertIn(agreement.access_token, center_url)
        self.assertIn("/convenio/firma-alumno/", student_url)
        self.assertIn(agreement.student_access_token, student_url)
        self.assertNotEqual(center_url, student_url)

    def test_center_signature_alone_does_not_complete(self):
        agreement = self._create_especifico()
        agreement.action_complete_signature(
            signature_base64=DUMMY_SIGNATURE,
            signer_name="Ana Representante",
            ip_address="192.168.1.10",
        )
        self.assertNotEqual(agreement.state, "completed")
        self.assertFalse(agreement.pdf_attachment_id)
        self.assertTrue(agreement.signature_center)

    def test_both_signatures_complete(self):
        agreement = self._create_especifico()
        agreement.action_complete_signature(
            signature_base64=DUMMY_SIGNATURE,
            signer_name="Ana Representante",
            ip_address="192.168.1.10",
        )
        agreement.action_complete_student_signature(
            signature_base64=DUMMY_SIGNATURE,
            signer_name="Alumno Prueba Específico",
            ip_address="192.168.1.20",
        )
        self.assertEqual(agreement.state, "completed")
        self.assertTrue(agreement.signature_student)
        self.assertTrue(agreement.pdf_attachment_id)
        self.assertIn("Especifico", agreement.pdf_attachment_id.name)
        self.assertNotIn("Marco", agreement.pdf_attachment_id.name)
        request_pdf = self.env["ir.attachment"].sudo().search([
            ("res_model", "=", "practice.request"),
            ("res_id", "=", self.request.id),
            ("mimetype", "=", "application/pdf"),
        ], limit=1)
        self.assertTrue(request_pdf)

    def test_wizard_creates_nacional(self):
        agreement = self._create_especifico(agreement_type="especifico_nacional")
        self.assertEqual(agreement.agreement_type, "especifico_nacional")
        self.assertEqual(agreement.practice_request_id, self.request)
        self.assertEqual(agreement.student_name, "Alumno Prueba Específico")
        self.assertTrue(agreement.student_access_token)

    def test_html_nacional_has_irg_insurance_not_abroad(self):
        agreement = self._create_especifico(agreement_type="especifico_nacional")
        html = self._render_agreement_html(agreement)
        self.assertIn("a cargo de iRG", html)
        self.assertIn("26/2015", html)
        self.assertIn("accidentes", html.lower())
        self.assertIn("asistencia sanitaria", html.lower())
        self.assertIn("Alumno Prueba Específico", html)
        self.assertIn("Centro Colaborador Test", html)
        self.assertNotIn("fuera de España", html)
        self.assertNotIn("Encuentro", html)
        self.assertNotIn("Miroslava", html)
        self.assertNotIn("INMIRA", html)

    def test_html_internacional_keeps_abroad_insurance(self):
        agreement = self._create_especifico()
        html = self._render_agreement_html(agreement)
        self.assertIn("fuera de España", html)
        self.assertNotIn("26/2015", html)

    def test_nacional_both_signatures_complete(self):
        agreement = self._create_especifico(agreement_type="especifico_nacional")
        agreement.action_complete_signature(
            signature_base64=DUMMY_SIGNATURE,
            signer_name="Ana Representante",
            ip_address="192.168.1.10",
        )
        self.assertNotEqual(agreement.state, "completed")
        agreement.action_complete_student_signature(
            signature_base64=DUMMY_SIGNATURE,
            signer_name="Alumno Prueba Específico",
            ip_address="192.168.1.20",
        )
        self.assertEqual(agreement.state, "completed")
        self.assertIn("Especifico_Nacional", agreement.pdf_attachment_id.name)
        self.assertNotIn("Marco", agreement.pdf_attachment_id.name)

    def test_marco_still_completes_with_center_only(self):
        agreement = self.env["practice.agreement"].create({
            "practice_center_id": self.center.id,
            "agreement_type": "marco_nacional",
        })
        agreement.action_complete_signature(
            signature_base64=DUMMY_SIGNATURE,
            signer_name="Ana Representante",
            ip_address="10.0.0.1",
        )
        self.assertEqual(agreement.state, "completed")
        self.assertTrue(agreement.pdf_attachment_id)
