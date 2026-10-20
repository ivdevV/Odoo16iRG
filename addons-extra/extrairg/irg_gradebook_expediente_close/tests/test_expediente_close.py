# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools.misc import format_date


ACADEMICA_EMAIL = "academica@institutoraimongaja.com"


class _FakeSMTP:
    def send_message(self, message, smtp_from=None, smtp_to=None):
        return {}

    def sendmail(self, smtp_from, smtp_to, message):
        return {}

    def quit(self):
        return None

    def close(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None


@tagged("post_install", "-at_install")
class TestExpedienteClose(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.product"].create(
            {
                "name": "IRG Expediente Close Product",
                "type": "service",
            }
        )
        cls.course_index = 0

    def _create_person(self, index):
        partner = self.env["res.partner"].create(
            {
                "name": "IRG Expediente Student %s" % index,
                "email": "irg.expediente.%s@example.com" % index,
            }
        )
        student = self.env["op.student"].create(
            {
                "partner_id": partner.id,
                "first_name": "IRG",
                "last_name": "Expediente %s" % index,
                "gender": "m",
            }
        )
        return partner, student

    def _create_open_gradebook(self, partner, student, application_number):
        type(self).course_index += 1
        index = type(self).course_index
        template = self.env["app.gradebook"].create(
            {
                "name": "IRG Expediente Template %s" % index,
                "gradebook_template_ids": [
                    (0, 0, {"type": "exam", "weight": 100.0, "qty": 1})
                ],
            }
        )
        course = self.env["op.course"].create(
            {
                "name": "IRG Expediente Course %s" % index,
                "code": "IRGEX%03d" % index,
                "gradebook_id": template.id,
                "lang": "en_US",
            }
        )
        register = self.env["op.admission.register"].create(
            {
                "name": "IRG Expediente Register %s" % index,
                "course_id": course.id,
                "product_id": self.product.id,
                "start_date": fields.Date.today(),
                "end_date": fields.Date.today(),
                "min_count": 1,
                "max_count": 100,
            }
        )
        admission = self.env["op.admission"].create(
            {
                "name": "IRG Expediente Admission %s" % index,
                "first_name": "IRG",
                "last_name": "Expediente %s" % index,
                "birth_date": "2000-01-01",
                "gender": "m",
                "email": partner.email,
                "partner_id": partner.id,
                "student_id": student.id,
                "course_id": course.id,
                "register_id": register.id,
                "application_number": application_number,
            }
        )
        gradebook = self.env["app.gradebook.student"].create(
            {
                "admission_id": admission.id,
                "state": "in_progress",
            }
        )
        subject = self.env["op.subject"].create(
            {
                "name": "IRG Expediente Subject %s" % index,
                "code": "IRGEX-S-%s" % index,
                "subject_type": "compulsory",
                "course_id": course.id,
            }
        )
        line = self.env["app.gradebook.subject"].create(
            {
                "gradebook_student_id": gradebook.id,
                "op_subject_id": subject.id,
            }
        )
        result = self.env["app.gradebook.result"].create(
            {
                "gradebook_subject_id": line.id,
                "survey_type": "exam",
                "scoring_total": 0.0,
            }
        )
        return gradebook, result

    def _mails_for(self, gradebook):
        return self.env["mail.mail"].search(
            [
                ("model", "=", "app.gradebook.student"),
                ("res_id", "=", gradebook.id),
                ("email_to", "=", ACADEMICA_EMAIL),
            ]
        )

    def _assert_notice(self, gradebook):
        self.assertEqual(gradebook.state, "done")
        self.assertEqual(
            gradebook.student_id.file_closing_date,
            fields.Date.context_today(gradebook),
        )
        mail = self._mails_for(gradebook)
        self.assertEqual(len(mail), 1)
        rendered_date = format_date(
            self.env,
            gradebook.student_id.file_closing_date,
            date_format="dd/MM/yyyy",
        )
        self.assertIn("CIERRE DE EXPEDIENTE", mail.subject)
        self.assertIn(gradebook.student_id.display_name, mail.subject)
        self.assertIn(gradebook.admission_id.application_number, mail.subject)
        self.assertIn(gradebook.course_id.display_name, mail.subject)
        self.assertEqual(mail.email_from, "Instituto Raimon Gaja <academica@institutoraimongaja.com>")
        body = str(mail.body_html)
        self.assertIn("CIERRE DE EXPEDIENTE", body)
        self.assertIn(gradebook.student_id.display_name, body)
        self.assertIn(gradebook.partner_id.email, body)
        self.assertIn(gradebook.course_id.display_name, body)
        self.assertIn(gradebook.admission_id.application_number, body)
        self.assertIn(gradebook.name, body)
        self.assertIn(rendered_date, body)

    def test_auto_close_stamps_empty_date_and_notifies(self):
        partner, student = self._create_person(1)
        gradebook, result = self._create_open_gradebook(partner, student, "AD-EXP-001")

        with patch.object(
            type(self.env["ir.mail_server"]),
            "connect",
            return_value=_FakeSMTP(),
        ):
            result.write({"scoring_total": 9.0})

        self._assert_notice(gradebook)

    def test_existing_date_is_kept_and_no_mail_is_sent(self):
        partner, student = self._create_person(2)
        student.file_closing_date = fields.Date.to_date("2020-01-15")
        gradebook, result = self._create_open_gradebook(partner, student, "AD-EXP-002")

        result.write({"scoring_total": 9.0})

        self.assertEqual(gradebook.state, "done")
        self.assertEqual(
            student.file_closing_date, fields.Date.to_date("2020-01-15")
        )
        self.assertFalse(self._mails_for(gradebook))

    def test_manual_done_does_not_stamp_or_notify(self):
        partner, student = self._create_person(3)
        gradebook, result = self._create_open_gradebook(
            partner, student, "AD-EXP-003"
        )
        self.env.cr.execute(
            "UPDATE app_gradebook_result SET scoring_total = 9 WHERE id = %s",
            [result.id],
        )
        result.invalidate_recordset(["scoring_total"])
        line = gradebook.gradebook_subject_ids
        line.invalidate_recordset()
        line.compute_final_subject_note()
        line.compute_point_average()
        self.assertTrue(gradebook._irg_is_ready_to_close())

        gradebook.state_to_done()

        self.assertEqual(gradebook.state, "done")
        self.assertFalse(student.file_closing_date)
        self.assertFalse(self._mails_for(gradebook))

    def test_mail_failure_keeps_close_and_date(self):
        partner, student = self._create_person(4)
        gradebook, result = self._create_open_gradebook(partner, student, "AD-EXP-004")

        def _raise_send(
            self,
            res_id,
            force_send=False,
            raise_exception=False,
            email_values=None,
            notif_layout=False,
        ):
            raise RuntimeError("smtp down")

        logger_name = (
            "odoo.addons.irg_gradebook_expediente_close.models.app_gradebook_student"
        )
        with self.assertLogs(logger_name, level="ERROR") as logged:
            with patch.object(
                type(self.env["mail.template"]), "send_mail", _raise_send
            ):
                result.write({"scoring_total": 9.0})

        self.assertTrue(any(str(gradebook.id) in line for line in logged.output))
        self.assertEqual(gradebook.state, "done")
        self.assertEqual(
            gradebook.student_id.file_closing_date,
            fields.Date.context_today(gradebook),
        )

    def test_two_gradebooks_same_student_send_one_notice(self):
        partner, student = self._create_person(5)
        first, first_result = self._create_open_gradebook(
            partner, student, "AD-EXP-005"
        )
        second, second_result = self._create_open_gradebook(
            partner, student, "AD-EXP-006"
        )

        with patch.object(
            type(self.env["ir.mail_server"]),
            "connect",
            return_value=_FakeSMTP(),
        ):
            (first_result | second_result).write({"scoring_total": 9.0})

        self.assertEqual(first.state, "done")
        self.assertEqual(second.state, "done")
        self.assertEqual(
            student.file_closing_date, fields.Date.context_today(first)
        )
        sent = self.env["mail.mail"].search(
            [
                ("model", "=", "app.gradebook.student"),
                ("res_id", "in", [first.id, second.id]),
                ("email_to", "=", ACADEMICA_EMAIL),
            ]
        )
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent.res_id, first.id)
        self.assertIn("AD-EXP-005", str(sent.body_html))

    def test_database_error_while_sending_keeps_close_and_date(self):
        partner, student = self._create_person(6)
        gradebook, result = self._create_open_gradebook(partner, student, "AD-EXP-007")

        def _abort(
            self,
            res_id,
            force_send=False,
            raise_exception=False,
            email_values=None,
            notif_layout=False,
        ):
            self.env.cr.execute("SELECT 1 FROM irg_expediente_missing_relation")

        with patch.object(type(self.env["mail.template"]), "send_mail", _abort):
            result.write({"scoring_total": 9.0})

        self.env.cr.execute("SELECT 1")
        gradebook.invalidate_recordset(["state"])
        student.invalidate_recordset(["file_closing_date"])
        self.assertEqual(gradebook.state, "done")
        self.assertEqual(
            gradebook.student_id.file_closing_date,
            fields.Date.context_today(gradebook),
        )

    def test_user_without_student_write_still_stamps(self):
        partner, student = self._create_person(7)
        gradebook, result = self._create_open_gradebook(partner, student, "AD-EXP-008")
        faculty = self.env.ref("openeducat_core.group_op_faculty")
        user = self.env["res.users"].create(
            {
                "name": "IRG Expediente Faculty",
                "login": "irg.expediente.faculty",
                "groups_id": [(6, 0, [faculty.id])],
            }
        )
        access = self.env.ref("openeducat_core.access_op_student_faculty")
        access.perm_write = False
        with self.assertRaises(AccessError):
            student.with_user(user).check_access_rights("write", raise_exception=True)

        with patch.object(
            type(self.env["ir.mail_server"]),
            "connect",
            return_value=_FakeSMTP(),
        ):
            result.with_user(user).write({"scoring_total": 9.0})

        self.assertEqual(gradebook.state, "done")
        self.assertEqual(
            student.file_closing_date, fields.Date.context_today(gradebook)
        )
        self.assertEqual(len(self._mails_for(gradebook)), 1)
