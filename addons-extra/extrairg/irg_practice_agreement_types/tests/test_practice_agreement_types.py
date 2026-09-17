# -*- coding: utf-8 -*-
from lxml import etree

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPracticeAgreementTypes(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "Centro Hospitalario de Prueba S.L.",
            "vat": "B12345678",
            "email": "contacto@hospitalprueba.com",
            "phone": "930001122",
        })
        cls.center = cls.env["practice.center"].create({
            "name": "Centro Hospitalario de Prueba",
            "official_name": "Centro Hospitalario de Prueba S.L.",
            "signatory_name": "Dr. Juan Pérez",
            "partner_id": cls.partner.id,
            "street": "Carrer Major 10",
            "city": "Barcelona",
            "postal_code": "08001",
            "email": "contacto@hospitalprueba.com",
            "phone": "930001122",
        })

    def _render_agreement_html(self, agreement):
        html, _fmt = self.env["ir.actions.report"]._render_qweb_html(
            "irg_practice_agreement_sign.action_report_practice_agreement",
            [agreement.id],
        )
        if isinstance(html, bytes):
            html = html.decode("utf-8")
        return str(html)

    def test_agreement_type_field_exists(self):
        field = self.env["practice.agreement"]._fields.get("agreement_type")
        self.assertIsNotNone(field)
        self.assertEqual(field.type, "selection")
        self.assertIn("marco_nacional", dict(field.selection))
        self.assertIn("marco_internacional", dict(field.selection))

    def test_wizard_model_exists(self):
        self.assertIn("irg.practice.agreement.create.wizard", self.env.registry)

    def test_center_button_opens_wizard(self):
        view_id = self.env.ref(
            "isep_practices_2.view_practice_center_form"
        ).id
        arch = self.env["practice.center"].get_view(
            view_id=view_id, view_type="form"
        )["arch"]
        root = etree.fromstring(arch.encode() if isinstance(arch, str) else arch)
        buttons = root.xpath(
            "//button[@name='action_open_create_agreement_wizard']"
        )
        self.assertTrue(
            buttons,
            "El formulario del centro debe abrir el wizard de crear convenio.",
        )
        self.assertEqual(buttons[0].get("string"), "Crear Convenio")
        old_create = root.xpath("//button[@name='action_create_agreement']")
        self.assertFalse(
            old_create,
            "El botón original 'Crear Convenio Marco' no debe quedar visible.",
        )

    def test_legacy_create_stays_nacional(self):
        action = self.center.action_create_agreement()
        agreement = self.env["practice.agreement"].browse(action["res_id"])
        self.assertNotEqual(agreement.agreement_type, "marco_internacional")
        html = self._render_agreement_html(agreement)
        self.assertNotIn("LATAM", html)
        self.assertNotIn("INMIRA", html)

    def test_wizard_creates_nacional_and_internacional(self):
        Wizard = self.env["irg.practice.agreement.create.wizard"]
        nacional = Wizard.create({
            "practice_center_id": self.center.id,
            "agreement_type": "marco_nacional",
        }).action_create_agreement()
        internacional = Wizard.create({
            "practice_center_id": self.center.id,
            "agreement_type": "marco_internacional",
        }).action_create_agreement()

        nac = self.env["practice.agreement"].browse(nacional["res_id"])
        inter = self.env["practice.agreement"].browse(internacional["res_id"])

        self.assertEqual(nacional["res_model"], "practice.agreement")
        self.assertEqual(nac.agreement_type, "marco_nacional")
        self.assertEqual(inter.agreement_type, "marco_internacional")
        self.assertEqual(inter.center_official_name, self.center.official_name)

        html_nac = self._render_agreement_html(nac)
        html_inter = self._render_agreement_html(inter)

        self.assertNotIn("LATAM", html_nac)
        self.assertIn("LATAM", html_inter)
        self.assertIn("4.3", html_inter)
        self.assertNotIn("INMIRA", html_inter)
        self.assertIn("Confidencialidad", html_inter)
        self.assertIn("Protección de datos", html_inter)

    def test_wizard_requires_center_and_type(self):
        Wizard = self.env["irg.practice.agreement.create.wizard"]
        field = Wizard._fields["agreement_type"]
        self.assertTrue(field.required)
        self.assertTrue(Wizard._fields["practice_center_id"].required)
        defaults = Wizard.default_get(["agreement_type"])
        self.assertEqual(defaults.get("agreement_type"), "marco_nacional")

    def test_cannot_change_type_after_sent(self):
        agreement = self.env["practice.agreement"].create({
            "practice_center_id": self.center.id,
            "agreement_type": "marco_nacional",
        })
        agreement.write({"agreement_type": "marco_internacional"})
        self.assertEqual(agreement.agreement_type, "marco_internacional")
        agreement.write({"state": "completed"})
        with self.assertRaises(UserError):
            agreement.write({"agreement_type": "marco_nacional"})
