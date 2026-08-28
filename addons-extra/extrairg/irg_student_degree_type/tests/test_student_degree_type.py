# -*- coding: utf-8 -*-

from lxml import etree

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStudentDegreeType(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "Alumno Tipo Titulación",
        })
        cls.student = cls.env["op.student"].create({
            "name": "Alumno Tipo Titulación",
            "first_name": "Alumno",
            "last_name": "Tipo Titulación",
            "partner_id": cls.partner.id,
        })

    def test_degree_type_model_has_name_and_color(self):
        degree_type = self.env["irg.student.degree.type"].create({
            "name": "Máster universitario",
            "color": 9,
        })
        self.assertEqual(degree_type.name, "Máster universitario")
        self.assertEqual(degree_type.color, 9)

    def test_student_field_is_many2many_towards_degree_type(self):
        field = self.env["op.student"]._fields.get("irg_degree_type_ids")
        self.assertIsNotNone(field)
        self.assertEqual(field.type, "many2many")
        self.assertEqual(field.comodel_name, "irg.student.degree.type")
        self.assertEqual(field.string, "Tipo de titulación")

    def test_student_persists_assigned_degree_types(self):
        own_title = self.env["irg.student.degree.type"].create({
            "name": "Título propio",
            "color": 3,
        })
        official = self.env["irg.student.degree.type"].create({
            "name": "Máster universitario",
            "color": 9,
        })
        self.student.write({
            "irg_degree_type_ids": [(6, 0, [own_title.id, official.id])],
        })
        self.assertEqual(self.student.irg_degree_type_ids, own_title | official)

    def test_form_shows_tags_widget_after_emergency_contact(self):
        arch = self.env["op.student"].get_view(view_type="form")["arch"]
        root = etree.fromstring(arch.encode() if isinstance(arch, str) else arch)
        page_fields = root.xpath(
            "//page[@name='personal_information']//field/@name"
        )
        self.assertIn("emergency_contact", page_fields)
        self.assertIn("irg_degree_type_ids", page_fields)
        self.assertGreater(
            page_fields.index("irg_degree_type_ids"),
            page_fields.index("emergency_contact"),
        )
        node = root.xpath(
            "//page[@name='personal_information']"
            "//field[@name='irg_degree_type_ids']"
        )[0]
        self.assertEqual(node.get("widget"), "many2many_tags")
        self.assertIn("color_field", node.get("options") or "")

    def test_internal_user_can_read_degree_type(self):
        degree_type = self.env["irg.student.degree.type"].create({
            "name": "Experto universitario",
            "color": 1,
        })
        user = self.env["res.users"].create({
            "name": "Lectura titulación",
            "login": "irg_degree_type_reader",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        degree_type.with_user(user).check_access_rights("read")
        degree_type.with_user(user).check_access_rule("read")

    def test_internal_user_cannot_unlink_degree_type(self):
        degree_type = self.env["irg.student.degree.type"].create({
            "name": "Diplomado",
            "color": 2,
        })
        user = self.env["res.users"].create({
            "name": "Sin borrar titulación",
            "login": "irg_degree_type_no_unlink",
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        with self.assertRaises(AccessError):
            degree_type.with_user(user).unlink()
