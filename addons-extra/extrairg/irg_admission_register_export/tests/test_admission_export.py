# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestAdmissionRegisterExportNationality(TransactionCase):

    def setUp(self):
        super().setUp()
        self.spain = self.env.ref("base.es")
        self.product = self.env["product.product"].create({
            "name": "Curso Export Nacionalidad",
            "type": "service",
            "list_price": 100.0,
        })
        self.course = self.env["op.course"].create({
            "name": "Curso Export Nacionalidad",
            "code": "AREXNAT01",
        })
        self.register = self.env["op.admission.register"].create({
            "name": "Registro Export Nacionalidad",
            "course_id": self.course.id,
            "product_id": self.product.id,
            "start_date": "2026-09-01",
            "end_date": "2026-09-30",
            "min_count": 1,
            "max_count": 100,
        })

    def _create_admission(self, **vals):
        values = {
            "first_name": "Ana",
            "last_name": "García",
            "name": "Ana García",
            "register_id": self.register.id,
            "course_id": self.course.id,
            "application_date": "2026-09-02",
            "birth_date": "1990-01-01",
            "gender": "f",
            "email": "ana.garcia.arexnat@example.com",
        }
        values.update(vals)
        return self.env["op.admission"].create(values)

    def _nationality_index(self, headers):
        self.assertIn("Nacionalidad", headers)
        return headers.index("Nacionalidad")

    def test_export_includes_student_nationality(self):
        partner = self.env["res.partner"].create({"name": "Ana García"})
        student = self.env["op.student"].create({
            "name": "Ana García",
            "first_name": "Ana",
            "last_name": "García",
            "partner_id": partner.id,
            "nationality": self.spain.id,
        })
        self._create_admission(
            partner_id=partner.id,
            student_id=student.id,
            is_student=True,
        )
        wizard = self.env["irg.admission.export.wizard"].create({
            "register_id": self.register.id,
            "export_format": "xlsx",
        })
        headers, rows = wizard._get_rows(self.register.admission_ids)
        idx = self._nationality_index(headers)
        self.assertEqual(headers[-1], "Nacionalidad")
        self.assertEqual(rows[0][idx], student.nationality.name)

    def test_export_nationality_empty_without_student_or_value(self):
        self._create_admission()
        partner = self.env["res.partner"].create({"name": "Luis Sin País"})
        student = self.env["op.student"].create({
            "name": "Luis Sin País",
            "first_name": "Luis",
            "last_name": "Sin País",
            "partner_id": partner.id,
        })
        self._create_admission(
            first_name="Luis",
            last_name="Sin País",
            name="Luis Sin País",
            email="luis.sinpais.arexnat@example.com",
            gender="m",
            partner_id=partner.id,
            student_id=student.id,
            is_student=True,
        )
        wizard = self.env["irg.admission.export.wizard"].create({
            "register_id": self.register.id,
            "export_format": "csv",
        })
        headers, rows = wizard._get_rows(self.register.admission_ids)
        idx = self._nationality_index(headers)
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row[idx] == "" for row in rows))
