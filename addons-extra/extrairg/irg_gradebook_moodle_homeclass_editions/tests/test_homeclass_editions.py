from datetime import date
from importlib import import_module
from unittest.mock import Mock, call, patch

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHomeClassEditions(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gradebook = cls.env["app.gradebook"].create(
            {
                "name": "Plantilla HomeClass Editions",
                "grading_scale": 10,
                "gradebook_template_ids": [
                    Command.create({"type": "exam", "weight": 100, "qty": 1})
                ],
            }
        )
        cls.course = cls.env["op.course"].create(
            {
                "name": "Curso HomeClass Editions",
                "code": "HC-EDITIONS",
                "lang": "en_US",
                "gradebook_id": cls.gradebook.id,
            }
        )
        cls.subject = cls.env["op.subject"].create(
            {
                "name": "Asignatura HomeClass Editions",
                "code": "HCE-01",
                "course_id": cls.course.id,
                "gradebook_id": cls.gradebook.id,
            }
        )
        cls.course.write({"subject_ids": [Command.link(cls.subject.id)]})
        cls.product = cls.env["product.product"].create(
            {"name": "HomeClass Editions Fee", "type": "service"}
        )
        cls.register = cls.env["op.admission.register"].create(
            {
                "name": "HomeClass Editions Register",
                "course_id": cls.course.id,
                "product_id": cls.product.id,
                "start_date": date(2026, 1, 1),
                "end_date": date(2026, 12, 31),
                "min_count": 1,
                "max_count": 30,
            }
        )
        cls.partner = cls.env["res.partner"].with_context(
            skip_moodle_sync=True
        ).create(
            {
                "name": "Alumno HomeClass Editions",
                "email": "homeclass.editions@example.com",
                "username": "homeclass.editions",
                "md_id": 880001,
            }
        )
        cls.student = cls.env["op.student"].create(
            {
                "first_name": "Alumno",
                "last_name": "HomeClass Editions",
                "gender": "o",
                "partner_id": cls.partner.id,
            }
        )
        cls.batch = cls.env["op.batch"].create(
            {
                "name": "Batch HomeClass Editions",
                "code": "PROMO-HC",
                "course_id": cls.course.id,
                "start_date": date(2025, 1, 1),
                "end_date": date(2025, 12, 31),
            }
        )
        cls.admission = cls.env["op.admission"].with_context(
            skip_moodle_sync=True
        ).create(
            {
                "name": "Alumno HomeClass Editions",
                "first_name": "Alumno",
                "last_name": "HomeClass Editions",
                "birth_date": date(1990, 1, 1),
                "gender": "o",
                "email": "homeclass.editions@example.com",
                "student_id": cls.student.id,
                "course_id": cls.course.id,
                "batch_id": cls.batch.id,
                "register_id": cls.register.id,
                "partner_id": cls.partner.id,
                "application_date": "2026-01-01 00:00:00",
                "admission_date": date(2025, 1, 1),
            }
        )
        cls.gradebook_student = cls.env["app.gradebook.student"].create(
            {"admission_id": cls.admission.id}
        )
        cls.env["app.gradebook.subject"].create(
            {
                "gradebook_student_id": cls.gradebook_student.id,
                "op_subject_id": cls.subject.id,
            }
        )

    def _course_map(self, name, moodle_course_id, **values):
        values.update(
            {
                "op_course_id": self.course.id,
                "moodle_course_id": moodle_course_id,
                "moodle_course_name": name,
            }
        )
        return self.env["irg.gradebook.moodle.course.map"].create(values)

    def _subject_map(self, course_map, activity_id):
        return self.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": self.subject.id,
                "moodle_course_id": course_map.moodle_course_id,
                "course_map_id": course_map.id,
                "line_ids": [
                    Command.create(
                        {
                            "moodle_activity_id": activity_id,
                            "activity_type": "quiz",
                        }
                    )
                ],
            }
        )

    def _wizard(self):
        return self.env["irg.gradebook.moodle.sync.wizard"].create(
            {"gradebook_student_id": self.gradebook_student.id}
        )

    def _assert_bridge_interfaces(self):
        course_map = self.env["irg.gradebook.moodle.course.map"]
        wizard = self.env["irg.gradebook.moodle.sync.wizard"]
        self.assertIn("irg_homeclass_edition_override", course_map._fields)
        self.assertTrue(hasattr(wizard, "_irg_homeclass_candidates"))
        self.assertTrue(hasattr(wizard, "_irg_order_homeclass_candidates"))
        self.assertTrue(hasattr(wizard, "_irg_load_multiple_homeclass"))

    @staticmethod
    def _usergrade(activity_id, grade=8):
        return [
            {
                "userid": 880001,
                "userfullname": "Alumno HomeClass Editions",
                "gradeitems": [
                    {
                        "id": activity_id,
                        "itemmodule": "quiz",
                        "itemname": "Examen HomeClass",
                        "graderaw": grade,
                        "grademax": 10,
                    }
                ],
            }
        ]

    def test_homeclass_periods_and_manual_override(self):
        self._assert_bridge_interfaces()
        module = import_module(
            "odoo.addons.irg_gradebook_moodle_homeclass_editions."
            "models.moodle_course_map"
        )
        for separator in ("-", "/", "_"):
            with self.subTest(separator=separator):
                name = "HomeClass 2025%s2026" % separator
                self.assertEqual(module.extract_homeclass_start_year(name), 2025)
                mapping = self._course_map(name, 910000 + ord(separator))
                self.assertEqual(mapping.edition_year, 2025)

        self.assertFalse(module.extract_homeclass_start_year("HC 2025-2027"))
        mapping = self._course_map("HomeClass sin periodo", 910100)
        mapping.irg_homeclass_edition_override = 2030
        self.assertEqual(mapping.edition_year, 2030)

    def test_homeclass_candidates_order_exact_generic_and_remaining(self):
        self._assert_bridge_interfaces()
        self.batch.code = "PROMO-HC"
        exact = self._course_map("HC 2025-2026", 35)
        generic = self._course_map("HC genérico", 50)
        remaining = self._course_map("HC 2024-2025", 36)
        wizard = self._wizard()

        candidates = wizard._irg_homeclass_candidates()
        self.assertEqual(
            wizard._irg_order_homeclass_candidates(candidates).ids,
            [exact.id, generic.id, remaining.id],
        )

    def test_multiple_homeclass_falls_back_when_first_course_has_no_activity(self):
        self._assert_bridge_interfaces()
        exact = self._course_map("HC 2025-2026", 35)
        fallback = self._course_map("HC 2024-2025", 36)
        self._subject_map(exact, 101)
        self._subject_map(fallback, 202)
        wizard = self._wizard()
        service = Mock()
        service.get_user_grade_items.side_effect = [
            ([{"userid": 880001, "userfullname": "Alumno", "gradeitems": []}], {}),
            (self._usergrade(202), {}),
        ]

        with patch(
            "odoo.addons.irg_gradebook_moodle_wizard.wizard."
            "moodle_sync_wizard.GradebookMoodleService",
            return_value=service,
        ), patch(
            "odoo.addons.odoo_moodle_connector.models.utils."
            "get_moodle_credentials",
            return_value={"access_token": "test", "base_url": "http://test"},
        ):
            self.assertTrue(wizard.action_load_moodle_data())

        self.assertEqual(service.get_user_grade_items.call_args_list, [call(35), call(36)])
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids.state, "ok")
        self.assertEqual(wizard.line_ids.moodle_grade, 8)

    def test_multiple_homeclass_stops_on_real_activity_collision(self):
        self._assert_bridge_interfaces()
        exact = self._course_map("HC 2025-2026", 35)
        fallback = self._course_map("HC 2024-2025", 36)
        self._subject_map(exact, 101)
        self._subject_map(fallback, 202)
        wizard = self._wizard()
        service = Mock()
        service.get_user_grade_items.side_effect = [
            (
                [
                    {
                        "userid": 880001,
                        "userfullname": "Alumno HomeClass Editions",
                        "gradeitems": [
                            {
                                "id": 101,
                                "itemmodule": "quiz",
                                "itemname": "Examen por ID",
                                "graderaw": 8,
                                "grademax": 10,
                            },
                            {
                                "cmid": 101,
                                "itemmodule": "quiz",
                                "itemname": "Examen por CMID",
                                "graderaw": 9,
                                "grademax": 10,
                            },
                        ],
                    }
                ],
                {},
            ),
            (self._usergrade(202), {}),
        ]

        with patch(
            "odoo.addons.irg_gradebook_moodle_wizard.wizard."
            "moodle_sync_wizard.GradebookMoodleService",
            return_value=service,
        ), patch(
            "odoo.addons.odoo_moodle_connector.models.utils."
            "get_moodle_credentials",
            return_value={"access_token": "test", "base_url": "http://test"},
        ):
            self.assertTrue(wizard.action_load_moodle_data())

        self.assertEqual(service.get_user_grade_items.call_args_list, [call(35)])
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids.state, "incompatible")
        self.assertFalse(wizard.line_ids.apply_line)
        self.assertIn("resolución ambigua", wizard.line_ids.moodle_info)

    def test_multiple_homeclass_uses_first_valid_course_without_mixing(self):
        self._assert_bridge_interfaces()
        exact = self._course_map("HC 2025-2026", 35)
        fallback = self._course_map("HC 2024-2025", 36)
        self._subject_map(exact, 101)
        self._subject_map(fallback, 202)
        wizard = self._wizard()
        service = Mock()
        service.get_user_grade_items.return_value = (self._usergrade(101, 7), {})

        with patch(
            "odoo.addons.irg_gradebook_moodle_wizard.wizard."
            "moodle_sync_wizard.GradebookMoodleService",
            return_value=service,
        ), patch(
            "odoo.addons.odoo_moodle_connector.models.utils."
            "get_moodle_credentials",
            return_value={"access_token": "test", "base_url": "http://test"},
        ):
            self.assertTrue(wizard.action_load_moodle_data())

        self.assertEqual(service.get_user_grade_items.call_args_list, [call(35)])
        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids.moodle_grade, 7)

    def test_online_delegates_to_existing_routing(self):
        self._assert_bridge_interfaces()
        self.batch.code = "PROMO-ONL"
        self._course_map("Online (ONLINE 2025)", 77)
        wizard = self._wizard()
        routing_module = import_module(
            "odoo.addons.irg_gradebook_moodle_routing.wizard.moodle_sync_wizard"
        )

        with patch.object(
            routing_module.IrgGradebookMoodleSyncWizard,
            "action_load_moodle_data",
            return_value="delegated",
        ) as delegated:
            self.assertEqual(wizard.action_load_moodle_data(), "delegated")

        delegated.assert_called_once()
