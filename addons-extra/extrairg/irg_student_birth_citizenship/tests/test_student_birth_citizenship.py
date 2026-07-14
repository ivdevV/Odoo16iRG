# -*- coding: utf-8 -*-

from lxml import etree

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStudentBirthCitizenship(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.spain = cls.env.ref("base.es")
        cls.france = cls.env.ref("base.fr")
        cls.partner = cls.env["res.partner"].create({"name": "Alumno Compartido"})
        cls.student = cls.env["op.student"].create({
            "name": "Alumno Compartido",
            "partner_id": cls.partner.id,
        })

    def test_partner_owns_the_three_fields_and_student_delegates_them(self):
        partner_fields = self.env["res.partner"]._fields
        student_fields = self.env["op.student"]._fields

        self.assertEqual(partner_fields["birth_place"].type, "char")
        self.assertEqual(
            partner_fields["birth_place"].string,
            "Población de nacimiento",
        )
        self.assertEqual(partner_fields["birth_country_id"].comodel_name, "res.country")
        self.assertEqual(
            partner_fields["birth_country_id"].string,
            "País de nacimiento",
        )
        self.assertEqual(
            partner_fields["citizenship_country_id"].comodel_name,
            "res.country",
        )
        self.assertEqual(
            partner_fields["citizenship_country_id"].string,
            "País de ciudadanía",
        )
        for field_name in (
            "birth_place",
            "birth_country_id",
            "citizenship_country_id",
        ):
            self.assertIn(field_name, student_fields)

    def test_values_written_from_student_are_stored_on_partner(self):
        self.student.write({
            "birth_place": "Madrid",
            "birth_country_id": self.spain.id,
            "citizenship_country_id": self.france.id,
        })

        self.assertEqual(self.partner.birth_place, "Madrid")
        self.assertEqual(self.partner.birth_country_id, self.spain)
        self.assertEqual(self.partner.citizenship_country_id, self.france)

    def test_values_written_from_partner_are_visible_on_student(self):
        self.partner.write({
            "birth_place": "París",
            "birth_country_id": self.france.id,
            "citizenship_country_id": self.spain.id,
        })

        self.assertEqual(self.student.birth_place, "París")
        self.assertEqual(self.student.birth_country_id, self.france)
        self.assertEqual(self.student.citizenship_country_id, self.spain)

    def test_both_forms_show_the_three_shared_fields(self):
        expected_fields = {
            "birth_place",
            "birth_country_id",
            "citizenship_country_id",
        }
        student_arch = self.env["op.student"].get_view(
            view_id=self.env.ref("openeducat_core.view_op_student_form").id,
            view_type="form",
        )["arch"]
        partner_arch = self.env["res.partner"].get_view(
            view_id=self.env.ref("base.view_partner_form").id,
            view_type="form",
        )["arch"]

        for arch in (student_arch, partner_arch):
            field_names = set(etree.fromstring(arch.encode()).xpath("//field/@name"))
            self.assertTrue(expected_fields.issubset(field_names))

    def test_existing_nationality_remains_independent(self):
        self.student.write({
            "nationality": self.spain.id,
            "citizenship_country_id": self.france.id,
        })

        self.assertEqual(self.student.nationality, self.spain)
        self.assertEqual(self.student.citizenship_country_id, self.france)
