from unittest.mock import Mock, patch
from types import SimpleNamespace

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.irg_gradebook_moodle_homeclass_editions.tests import (
    test_homeclass_editions,
)

_HomeClassEditionsCase = test_homeclass_editions.TestHomeClassEditions


@tagged("post_install", "-at_install")
class TestIteminstanceMatcher(TransactionCase):
    def setUp(self):
        super().setUp()
        self.wizard = self.env["irg.gradebook.moodle.sync.wizard"]

    def test_matches_activity_by_iteminstance(self):
        item = {"id": 555, "cmid": 3290, "iteminstance": 205}

        result = self.wizard._irg_match_grade_items([item], 205)

        self.assertEqual([(0, item)], result)

    def test_same_item_matching_two_fields_is_not_ambiguous(self):
        item = {"id": 205, "cmid": 3290, "iteminstance": 205}

        result = self.wizard._irg_match_grade_items([item], 205)

        self.assertEqual([(0, item)], result)

    def test_different_items_across_namespaces_are_ambiguous(self):
        items = [
            {"id": 205, "cmid": 3290, "iteminstance": 999},
            {"id": 777, "cmid": 888, "iteminstance": 205},
        ]

        result = self.wizard._irg_match_grade_items(items, 205)

        self.assertEqual([(0, items[0]), (1, items[1])], result)


@tagged("post_install", "-at_install")
class TestIteminstanceService(TransactionCase):
    @staticmethod
    def _payload(iteminstance):
        return {
            "usergrades": [
                {
                    "userid": 777,
                    "userfullname": "Alumno",
                    "gradeitems": [
                        {
                            "id": 555,
                            "cmid": 3290,
                            "iteminstance": iteminstance,
                            "itemname": "Actividad",
                            "itemmodule": "quiz",
                            "graderaw": 8.0,
                            "grademax": 10.0,
                        }
                    ],
                }
            ]
        }

    def _service(self):
        wizard = self.env["irg.gradebook.moodle.sync.wizard"]
        with patch(
            "odoo.addons.irg_gradebook_moodle_wizard.wizard."
            "moodle_sync_wizard.connector_utils.get_moodle_credentials",
            return_value={
                "access_token": "test-token",
                "base_url": "https://moodle.example",
            },
        ):
            return wizard._get_service()

    def test_rejects_non_integer_iteminstance(self):
        with self.assertRaisesRegex(
            UserError, "respuesta recibida de Moodle no es válida"
        ):
            self._service()._validate_grade_payload(
                self._payload(iteminstance="205")
            )

    def test_accepts_integer_null_and_zero_iteminstance(self):
        service = self._service()
        for value in (205, None, 0):
            with self.subTest(iteminstance=value):
                payload = self._payload(iteminstance=value)
                self.assertEqual(
                    payload["usergrades"],
                    service._validate_grade_payload(payload),
                )

    def test_preserves_injected_base_service(self):
        injected_service = Mock()
        wizard = self.env["irg.gradebook.moodle.sync.wizard"]

        with patch(
            "odoo.addons.irg_gradebook_moodle_wizard.wizard."
            "moodle_sync_wizard.GradebookMoodleService",
            return_value=injected_service,
        ), patch(
            "odoo.addons.odoo_moodle_connector.models.utils."
            "get_moodle_credentials",
            return_value={
                "access_token": "test-token",
                "base_url": "https://moodle.example",
            },
        ):
            service = wizard._get_service()

        self.assertIs(injected_service, service)


@tagged("post_install", "-at_install")
class TestIteminstanceGradeAggregation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.wizard = self.env["irg.gradebook.moodle.sync.wizard"]

    @staticmethod
    def _line(activity_id, activity_type="quiz"):
        return SimpleNamespace(
            moodle_activity_id=activity_id,
            activity_type=activity_type,
        )

    @staticmethod
    def _item(**values):
        item = {
            "id": 555,
            "cmid": 3290,
            "iteminstance": 205,
            "itemname": "Actividad real",
            "itemmodule": "quiz",
            "graderaw": 8.0,
            "grademax": 10.0,
        }
        item.update(values)
        return item

    def _resolve(self, items, lines):
        return self.wizard._grades_by_type(
            {"gradeitems": items}, lines, grading_scale=10.0
        )["exam"]

    def test_aggregates_grade_matched_by_iteminstance(self):
        result = self._resolve([self._item()], [self._line(205)])

        self.assertEqual(8.0, result["avg"])
        self.assertEqual(1, result["graded"])
        self.assertFalse(result["error"])

    def test_zero_matches_is_reported_as_not_found(self):
        result = self._resolve([self._item()], [self._line(999)])

        self.assertIn("No se encontró", result["error"])
        self.assertNotIn("ambigua", result["error"])

    def test_collision_between_id_and_iteminstance_is_ambiguous(self):
        items = [
            self._item(id=205, iteminstance=900),
            self._item(id=777, cmid=888, iteminstance=205),
        ]

        result = self._resolve(items, [self._line(205)])

        self.assertTrue(result["error"])
        self.assertIn("resolución ambigua", result["error"])
        self.assertIsNone(result["avg"])

    def test_iteminstance_match_still_validates_activity_type(self):
        result = self._resolve(
            [self._item(itemmodule="assign")], [self._line(205)]
        )

        self.assertIn("no coincide con el tipo", result["error"])
        self.assertIsNone(result["avg"])

    def test_id_and_cmid_matching_remain_compatible(self):
        for activity_id in (555, 3290):
            with self.subTest(activity_id=activity_id):
                result = self._resolve(
                    [self._item()], [self._line(activity_id)]
                )
                self.assertEqual(8.0, result["avg"])
                self.assertFalse(result["error"])

    def test_same_item_reused_by_two_map_lines_is_ambiguous(self):
        result = self._resolve(
            [self._item()], [self._line(555), self._line(205)]
        )

        self.assertIn("mismo grade item se reutiliza", result["error"])
        self.assertIsNone(result["avg"])

    def test_homeclass_conflict_detects_cross_namespace_collision(self):
        conflict = self.wizard._irg_resolution_conflict(
            {
                "gradeitems": [
                    self._item(id=205, iteminstance=900),
                    self._item(id=777, cmid=888, iteminstance=205),
                ]
            },
            [self._line(205)],
        )

        self.assertTrue(conflict)
        self.assertIn("resolución ambigua", conflict)


@tagged("post_install", "-at_install")
class TestIteminstanceHomeClassFallback(_HomeClassEditionsCase):
    @staticmethod
    def _iteminstance_usergrade(activity_id, activity_type="quiz", grade=8):
        return [
            {
                "userid": 880001,
                "userfullname": "Alumno HomeClass Editions",
                "gradeitems": [
                    {
                        "id": 555,
                        "cmid": 3290,
                        "iteminstance": activity_id,
                        "itemmodule": activity_type,
                        "itemname": "Examen por iteminstance",
                        "graderaw": grade,
                        "grademax": 10,
                    }
                ],
            }
        ]

    def _load_with_service(self, wizard, service):
        with patch(
            "odoo.addons.irg_gradebook_moodle_wizard.wizard."
            "moodle_sync_wizard.GradebookMoodleService",
            return_value=service,
        ), patch(
            "odoo.addons.odoo_moodle_connector.models.utils."
            "get_moodle_credentials",
            return_value={"access_token": "test", "base_url": "http://test"},
        ):
            return wizard.action_load_moodle_data()

    def test_multiple_homeclass_falls_back_to_iteminstance_match(self):
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
                        "userfullname": "Alumno",
                        "gradeitems": [],
                    }
                ],
                {},
            ),
            (self._iteminstance_usergrade(202), {}),
        ]

        self.assertTrue(self._load_with_service(wizard, service))

        called_courses = [
            args[0][0]
            for args in service.get_user_grade_items.call_args_list
        ]
        self.assertEqual([35, 36], called_courses)
        self.assertEqual("ok", wizard.line_ids.state)
        self.assertEqual(8, wizard.line_ids.moodle_grade)

    def test_iteminstance_type_conflict_stops_before_fallback(self):
        exact = self._course_map("HC 2025-2026", 35)
        fallback = self._course_map("HC 2024-2025", 36)
        self._subject_map(exact, 101)
        self._subject_map(fallback, 202)
        wizard = self._wizard()
        service = Mock()
        service.get_user_grade_items.side_effect = [
            (self._iteminstance_usergrade(101, activity_type="assign"), {}),
            (self._iteminstance_usergrade(202), {}),
        ]

        self.assertTrue(self._load_with_service(wizard, service))

        called_courses = [
            args[0][0]
            for args in service.get_user_grade_items.call_args_list
        ]
        self.assertEqual([35], called_courses)
        self.assertEqual("incompatible", wizard.line_ids.state)
        self.assertIn("no coincide con el tipo", wizard.line_ids.moodle_info)
