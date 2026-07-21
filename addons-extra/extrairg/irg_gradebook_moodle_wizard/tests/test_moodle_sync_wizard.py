from datetime import date
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


SERVICE_PATH = (
    "odoo.addons.irg_gradebook_moodle_wizard.wizard.moodle_sync_wizard"
)

REQUIRED_MODELS = (
    "irg.gradebook.moodle.map",
    "irg.gradebook.moodle.map.line",
    "irg.gradebook.moodle.sync.wizard",
    "irg.gradebook.moodle.sync.wizard.line",
)


def _fake_usergrades(md_user_id=777):
    return [
        {
            "userid": md_user_id,
            "userfullname": "Alumno De Prueba",
            "gradeitems": [
                {
                    "id": 395,
                    "cmid": 4395,
                    "itemname": "TEST 1.1",
                    "itemmodule": "quiz",
                    "graderaw": 8.0,
                    "grademax": 10.0,
                },
                {
                    "id": 397,
                    "cmid": 4397,
                    "itemname": "TEST 1.2",
                    "itemmodule": "quiz",
                    "graderaw": 90.0,
                    "grademax": 100.0,
                },
                {
                    "id": 500,
                    "cmid": 4500,
                    "itemname": "Tarea 1",
                    "itemmodule": "assign",
                    "graderaw": None,
                    "grademax": 10.0,
                },
            ],
        }
    ]


@tagged("post_install", "-at_install")
class TestMoodleSyncWizard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._missing_models = [
            model_name
            for model_name in REQUIRED_MODELS
            if model_name not in cls.env.registry.models
        ]
        if cls._missing_models:
            return

        cls.gradebook = cls.env["app.gradebook"].create(
            {
                "name": "Plantilla Test Moodle",
                "grading_scale": 10,
                "gradebook_template_ids": [
                    (
                        0,
                        0,
                        {"type": "exam", "weight": 100, "qty": 1},
                    )
                ],
            }
        )
        cls.course = cls.env["op.course"].create(
            {
                "name": "Curso Test Moodle",
                "code": "CTM-WIZ",
                "gradebook_id": cls.gradebook.id,
            }
        )
        cls.subject = cls.env["op.subject"].create(
            {
                "name": "Asignatura Test Moodle",
                "code": "AT01-WIZ",
                "course_id": cls.course.id,
                "gradebook_id": cls.gradebook.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Moodle Wizard Fee", "type": "service"}
        )
        cls.register = cls.env["op.admission.register"].create(
            {
                "name": "Moodle Wizard Register",
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
                "name": "Alumno De Prueba",
                "email": "alumno.test@example.com",
                "username": "alumno.test",
                "md_id": 777,
            }
        )
        cls.student = cls.env["op.student"].create(
            {
                "first_name": "Alumno",
                "last_name": "De Prueba",
                "gender": "o",
                "partner_id": cls.partner.id,
            }
        )
        cls.batch = cls.env["op.batch"].create(
            {
                "name": "Batch Test Moodle",
                "code": "BT01-WIZ",
                "course_id": cls.course.id,
                "start_date": date(2026, 1, 1),
                "end_date": date(2026, 12, 31),
            }
        )
        cls.admission = cls.env["op.admission"].with_context(
            skip_moodle_sync=True
        ).create(
            {
                "name": "Alumno De Prueba",
                "first_name": "Alumno",
                "last_name": "De Prueba",
                "birth_date": date(1990, 1, 1),
                "gender": "o",
                "email": "alumno.test@example.com",
                "student_id": cls.student.id,
                "course_id": cls.course.id,
                "batch_id": cls.batch.id,
                "register_id": cls.register.id,
                "partner_id": cls.partner.id,
                "admission_date": date(2026, 1, 1),
            }
        )
        cls.gb_student = cls.env["app.gradebook.student"].create(
            {"admission_id": cls.admission.id}
        )
        cls.gb_subject = cls.env["app.gradebook.subject"].create(
            {
                "gradebook_student_id": cls.gb_student.id,
                "op_subject_id": cls.subject.id,
            }
        )
        cls.map = cls.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": cls.subject.id,
                "moodle_course_id": 44,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "moodle_activity_id": 395,
                            "activity_type": "quiz",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "moodle_activity_id": 397,
                            "activity_type": "quiz",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "moodle_activity_id": 500,
                            "activity_type": "assign",
                        },
                    ),
                ],
            }
        )

    def _skip_until_models_exist(self):
        if self._missing_models:
            self.skipTest(
                "TDD RED pendiente de modelos: %s"
                % ", ".join(self._missing_models)
            )

    def _open_wizard(self, usergrades=None, emails=None):
        usergrades = usergrades if usergrades is not None else _fake_usergrades()
        emails = emails or {777: "alumno.test@example.com"}
        with patch(SERVICE_PATH + ".GradebookMoodleService") as mock_service, patch(
            "odoo.addons.odoo_moodle_connector.models.utils."
            "get_moodle_credentials",
            return_value={"access_token": "x", "base_url": "http://test"},
        ):
            mock_service.return_value.get_user_grade_items.return_value = (
                usergrades,
                emails,
            )
            wizard = self.env["irg.gradebook.moodle.sync.wizard"].create(
                {"gradebook_student_id": self.gb_student.id}
            )
            wizard.action_load_moodle_data()
        return wizard

    def test_load_ok_exam_average_and_scale(self):
        """Dos quizzes con nota (8/10 y 90/100) -> media exam 8.5."""
        self.assertFalse(
            self._missing_models,
            "TDD RED: faltan modelos del addon: %s"
            % ", ".join(self._missing_models),
        )
        wizard = self._open_wizard()
        exam = wizard.line_ids.filtered(lambda line: line.survey_type == "exam")
        self.assertEqual(len(exam), 1)
        self.assertEqual(exam.state, "ok")
        self.assertAlmostEqual(exam.moodle_grade, 8.5, places=2)
        self.assertEqual(exam.graded_count, 2)
        self.assertEqual(wizard.match_method, "md_id")

    def test_load_assign_without_grade(self):
        """La tarea mapeada sin graderaw -> línea sin_nota, no aplicable."""
        self._skip_until_models_exist()
        wizard = self._open_wizard()
        assign = wizard.line_ids.filtered(
            lambda line: line.survey_type == "assignment"
        )
        self.assertEqual(assign.state, "sin_nota")
        self.assertFalse(assign.apply_line)

    def test_load_no_map(self):
        """Asignatura sin mapeo -> línea sin_mapeo."""
        self._skip_until_models_exist()
        self.map.active = False
        wizard = self._open_wizard()
        self.assertEqual(wizard.line_ids.state, "sin_mapeo")

    def test_load_student_not_found(self):
        """Sin md_id, email ni nombre coincidente -> alumno_no_encontrado."""
        self._skip_until_models_exist()
        self.partner.with_context(skip_moodle_sync=True).write({"md_id": False})
        wizard = self._open_wizard(
            usergrades=[
                {
                    "userid": 999,
                    "userfullname": "Otra Persona",
                    "gradeitems": [],
                }
            ],
            emails={999: "otra@example.com"},
        )
        self.assertEqual(wizard.line_ids.state, "alumno_no_encontrado")

    def test_match_by_cmid(self):
        """IDs del mapeo como cmid (no grade item id) también matchean."""
        self._skip_until_models_exist()
        self.map.line_ids.unlink()
        self.env["irg.gradebook.moodle.map.line"].create(
            {
                "map_id": self.map.id,
                "moodle_activity_id": 4395,
                "activity_type": "quiz",
            }
        )
        wizard = self._open_wizard()
        exam = wizard.line_ids.filtered(lambda line: line.survey_type == "exam")
        self.assertEqual(exam.state, "ok")
        self.assertAlmostEqual(exam.moodle_grade, 8.0, places=2)

    def test_apply_creates_and_upserts(self):
        """Aplicar crea la línea de resultado; re-aplicar la actualiza."""
        self._skip_until_models_exist()
        wizard = self._open_wizard()
        wizard.action_apply()
        result = self.env["app.gradebook.result"].search(
            [
                ("gradebook_subject_id", "=", self.gb_subject.id),
                ("is_moodle", "=", True),
                ("survey_type", "=", "exam"),
            ]
        )
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result.scoring_total, 8.5, places=2)

        wizard2 = self._open_wizard()
        exam2 = wizard2.line_ids.filtered(
            lambda line: line.survey_type == "exam"
        )
        exam2.grade_to_apply = 9.0
        wizard2.action_apply()
        result2 = self.env["app.gradebook.result"].search(
            [
                ("gradebook_subject_id", "=", self.gb_subject.id),
                ("is_moodle", "=", True),
                ("survey_type", "=", "exam"),
            ]
        )
        self.assertEqual(len(result2), 1)
        self.assertAlmostEqual(result2.scoring_total, 9.0, places=2)

    def test_apply_recomputes_subject_average(self):
        """Tras aplicar, el AVG de exámenes de la asignatura refleja la nota."""
        self._skip_until_models_exist()
        wizard = self._open_wizard()
        wizard.action_apply()
        self.gb_subject.invalidate_recordset()
        self.assertAlmostEqual(self.gb_subject.point_average_exam, 8.5, places=2)
