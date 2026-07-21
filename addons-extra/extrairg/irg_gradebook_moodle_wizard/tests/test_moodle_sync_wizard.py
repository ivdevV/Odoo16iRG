from datetime import date
import threading
import uuid
from unittest.mock import patch

from psycopg2 import IntegrityError
from psycopg2.errors import SerializationFailure

from odoo import Command, api
from odoo.exceptions import AccessError, UserError
from odoo.service import model as service_model
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
                        {"type": "exam", "weight": 50, "qty": 1},
                    ),
                    (
                        0,
                        0,
                        {"type": "assignment", "weight": 50, "qty": 1},
                    ),
                ],
            }
        )
        cls.course = cls.env["op.course"].create(
            {
                "name": "Curso Test Moodle",
                "code": "CTM-WIZ",
                "lang": "en_US",
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
        cls.internal_user = cls.env["res.users"].with_context(
            no_reset_password=True
        ).create(
            {
                "name": "Moodle Wizard Internal",
                "login": "moodle-wizard-internal",
                "email": "moodle-wizard-internal@example.com",
                "groups_id": [
                    Command.set([cls.env.ref("base.group_user").id])
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

    def test_apply_accepts_locked_lines_with_different_functional_order(self):
        """El orden funcional no simula altas o borrados concurrentes."""
        wizard = self.env["irg.gradebook.moodle.sync.wizard"].create(
            {"gradebook_student_id": self.gb_student.id}
        )
        line_model = self.env["irg.gradebook.moodle.sync.wizard.line"]
        exam = line_model.create(
            {
                "wizard_id": wizard.id,
                "gradebook_subject_id": self.gb_subject.id,
                "subject_id": self.subject.id,
                "survey_type": "exam",
                "grade_to_apply": 8.0,
                "graded_count": 1,
                "state": "ok",
                "apply_line": True,
            }
        )
        assignment = line_model.create(
            {
                "wizard_id": wizard.id,
                "gradebook_subject_id": self.gb_subject.id,
                "subject_id": self.subject.id,
                "survey_type": "assignment",
                "state": "ok",
                "apply_line": False,
            }
        )
        self.assertLess(exam.id, assignment.id)
        wizard.invalidate_recordset(["line_ids"])
        self.assertEqual(wizard.line_ids.ids, [assignment.id, exam.id])

        wizard.action_apply()

        result = self.env["app.gradebook.result"].search(
            [
                ("gradebook_subject_id", "=", self.gb_subject.id),
                ("survey_type", "=", "exam"),
                ("is_moodle", "=", True),
            ]
        )
        self.assertEqual(len(result), 1)
        self.assertAlmostEqual(result.scoring_total, 8.0, places=2)

    def test_apply_recomputes_subject_average(self):
        """Tras aplicar, el AVG de exámenes de la asignatura refleja la nota."""
        self._skip_until_models_exist()
        wizard = self._open_wizard()
        wizard.action_apply()
        self.gb_subject.invalidate_recordset()
        self.assertAlmostEqual(self.gb_subject.point_average_exam, 8.5, places=2)

    def test_template_qty_greater_than_one_is_incompatible(self):
        """El upsert agregado no puede representar templates con qty != 1."""
        exam_template = self.gradebook.gradebook_template_ids.filtered(
            lambda line: line.type == "exam"
        )
        exam_template.qty = 2

        wizard = self._open_wizard()
        exam = wizard.line_ids.filtered(lambda line: line.survey_type == "exam")

        self.assertEqual(exam.state, "incompatible")
        self.assertFalse(exam.apply_line)
        self.assertIn("cantidad", exam.moodle_info.lower())

    def test_manual_result_of_same_type_is_incompatible(self):
        """Una nota manual del mismo tipo nunca se mezcla con el agregado Moodle."""
        self.env["app.gradebook.result"].create(
            {
                "gradebook_subject_id": self.gb_subject.id,
                "survey_type": "exam",
                "scoring_total": 6.0,
                "description": "Nota manual existente",
            }
        )

        wizard = self._open_wizard()
        exam = wizard.line_ids.filtered(lambda line: line.survey_type == "exam")

        self.assertEqual(exam.state, "incompatible")
        self.assertFalse(exam.apply_line)
        self.assertIn("manual", exam.moodle_info.lower())

    def test_invalid_grade_max_values_produce_no_grade(self):
        """Máximos ausentes, cero o negativos no aportan una nota escalada."""
        self.map.line_ids.filtered(
            lambda line: line.activity_type == "quiz"
        )[1:].unlink()
        for grade_max in (None, 0, -10):
            with self.subTest(grade_max=grade_max):
                usergrades = _fake_usergrades()
                usergrades[0]["gradeitems"] = [
                    {
                        "id": 395,
                        "cmid": 4395,
                        "itemname": "TEST máximo inválido",
                        "itemmodule": "quiz",
                        "graderaw": 8.0,
                        "grademax": grade_max,
                    }
                ]
                wizard = self._open_wizard(usergrades=usergrades)
                exam = wizard.line_ids.filtered(
                    lambda line: line.survey_type == "exam"
                )
                self.assertEqual(exam.state, "sin_nota")
                self.assertFalse(exam.apply_line)

    def test_multiple_active_maps_are_incompatible(self):
        """Dos mapas activos para una asignatura no se resuelven arbitrariamente."""
        self.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": self.subject.id,
                "moodle_course_id": 45,
                "line_ids": [
                    Command.create(
                        {
                            "moodle_activity_id": 395,
                            "activity_type": "quiz",
                        }
                    )
                ],
            }
        )

        wizard = self._open_wizard()

        self.assertEqual(len(wizard.line_ids), 1)
        self.assertEqual(wizard.line_ids.state, "incompatible")
        self.assertFalse(wizard.line_ids.apply_line)
        self.assertIn("mapa", wizard.line_ids.moodle_info.lower())

    def test_multiple_empty_active_maps_remain_incompatible(self):
        """La ambigüedad de mapas prevalece aunque ninguno tenga líneas."""
        self.map.line_ids.unlink()
        self.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": self.subject.id,
                "moodle_course_id": 46,
            }
        )

        wizard = self._open_wizard()

        self.assertEqual(wizard.line_ids.state, "incompatible")
        self.assertFalse(wizard.line_ids.apply_line)

    def test_id_cmid_collision_invalidates_complete_type(self):
        """Un grade item reutilizado por dos líneas invalida toda la media."""
        self.map.line_ids.unlink()
        self.map.write(
            {
                "line_ids": [
                    Command.create(
                        {"moodle_activity_id": 395, "activity_type": "quiz"}
                    ),
                    Command.create(
                        {"moodle_activity_id": 4395, "activity_type": "quiz"}
                    ),
                ]
            }
        )
        usergrades = _fake_usergrades()
        usergrades[0]["gradeitems"] = [usergrades[0]["gradeitems"][0]]

        wizard = self._open_wizard(usergrades=usergrades)
        exam = wizard.line_ids.filtered(lambda line: line.survey_type == "exam")

        self.assertEqual(exam.state, "incompatible")
        self.assertFalse(exam.apply_line)
        self.assertIn("ambigua", exam.moodle_info.lower())

    def test_internal_user_cannot_open_load_or_apply(self):
        """Los tres entry points aplican autorización server-side."""
        wizard = self.env["irg.gradebook.moodle.sync.wizard"].create(
            {"gradebook_student_id": self.gb_student.id}
        )

        with self.assertRaises(AccessError):
            self.gb_student.with_user(
                self.internal_user
            ).action_open_moodle_sync_wizard()
        with self.assertRaises(AccessError):
            wizard.with_user(self.internal_user).action_load_moodle_data()
        with self.assertRaises(AccessError):
            wizard.with_user(self.internal_user).action_apply()

    def test_moodle_sync_key_is_unique_and_manual_results_remain_multiple(self):
        """La clave nullable bloquea Moodle duplicado sin afectar notas manuales."""
        self.assertIn(
            "moodle_sync_key", self.env["app.gradebook.result"]._fields
        )
        values = {
            "gradebook_subject_id": self.gb_subject.id,
            "survey_type": "exam",
            "scoring_total": 7.0,
        }
        self.env["app.gradebook.result"].create(values)
        self.env["app.gradebook.result"].create(values)
        self.assertEqual(
            self.env["app.gradebook.result"].search_count(
                [
                    ("gradebook_subject_id", "=", self.gb_subject.id),
                    ("survey_type", "=", "exam"),
                    ("is_moodle", "=", False),
                ]
            ),
            2,
        )

        moodle_values = dict(values, is_moodle=True)
        self.env["app.gradebook.result"].create(moodle_values)
        with self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self.env["app.gradebook.result"].create(moodle_values)

    def test_apply_rejects_non_finite_and_out_of_scale_grades(self):
        """La nota editable se valida en servidor antes de escribir."""
        wizard = self._open_wizard()
        exam = wizard.line_ids.filtered(lambda line: line.survey_type == "exam")

        for invalid_grade in (float("nan"), float("inf"), -0.01, 10.01):
            with self.subTest(invalid_grade=invalid_grade):
                exam.grade_to_apply = invalid_grade
                with self.assertRaises(UserError):
                    wizard.action_apply()

    def test_apply_rejects_forced_non_ok_line(self):
        """RPC/ORM no puede convertir una línea sin nota en aplicable."""
        wizard = self._open_wizard()
        assignment = wizard.line_ids.filtered(
            lambda line: line.survey_type == "assignment"
        )
        self.assertEqual(assignment.state, "sin_nota")
        assignment.write({"apply_line": True, "grade_to_apply": 7.0})

        with self.assertRaises(UserError):
            wizard.action_apply()

        self.assertFalse(
            self.env["app.gradebook.result"].search(
                [
                    ("gradebook_subject_id", "=", self.gb_subject.id),
                    ("survey_type", "=", "assignment"),
                    ("is_moodle", "=", True),
                ]
            )
        )

    def test_apply_rejects_legacy_duplicate_moodle_results(self):
        """Duplicados legados con clave nula abortan toda la aplicación."""
        wizard = self._open_wizard()
        self.env["app.gradebook.result"].create(
            {
                "gradebook_subject_id": self.gb_subject.id,
                "survey_type": "exam",
                "scoring_total": 7.0,
                "is_moodle": True,
            }
        )
        self.env.cr.execute(
            """
            INSERT INTO app_gradebook_result (
                gradebook_subject_id, survey_type, scoring_total, is_moodle,
                create_uid, write_uid, create_date, write_date
            ) VALUES (%s, 'exam', 6.0, TRUE, %s, %s, NOW(), NOW())
            RETURNING id
            """,
            (self.gb_subject.id, self.env.uid, self.env.uid),
        )
        duplicate_id = self.env.cr.fetchone()[0]
        try:
            with self.assertRaises(UserError):
                wizard.action_apply()
        finally:
            self.env.cr.execute(
                "DELETE FROM app_gradebook_result WHERE id = %s",
                (duplicate_id,),
            )

    def test_unselected_legacy_duplicate_aborts_complete_apply(self):
        """La integridad global se valida aunque la línea duplicada no se aplique."""
        wizard = self._open_wizard()
        assignment_line = wizard.line_ids.filtered(
            lambda line: line.survey_type == "assignment"
        )
        assignment_line.apply_line = False
        self.env["app.gradebook.result"].create(
            {
                "gradebook_subject_id": self.gb_subject.id,
                "survey_type": "assignment",
                "scoring_total": 7.0,
                "is_moodle": True,
            }
        )
        self.env.cr.execute(
            """
            INSERT INTO app_gradebook_result (
                gradebook_subject_id, survey_type, scoring_total, is_moodle,
                create_uid, write_uid, create_date, write_date
            ) VALUES (%s, 'assignment', 6.0, TRUE, %s, %s, NOW(), NOW())
            RETURNING id
            """,
            (self.gb_subject.id, self.env.uid, self.env.uid),
        )
        duplicate_id = self.env.cr.fetchone()[0]
        try:
            with self.assertRaises(UserError):
                wizard.action_apply()
        finally:
            self.env.cr.execute(
                "DELETE FROM app_gradebook_result WHERE id = %s",
                (duplicate_id,),
            )

    def _create_committed_concurrency_case(self):
        registry = self.env.registry
        suffix = uuid.uuid4().hex[:8]
        with registry.cursor() as setup_cr:
            setup_env = api.Environment(
                setup_cr, self.env.ref("base.user_admin").id, {}
            )
            gradebook = setup_env["app.gradebook"].create(
                {
                    "name": "Concurrent Moodle %s" % suffix,
                    "grading_scale": 10,
                    "gradebook_template_ids": [
                        Command.create(
                            {"type": "exam", "weight": 100, "qty": 1}
                        )
                    ],
                }
            )
            course = setup_env["op.course"].create(
                {
                    "name": "Concurrent Moodle %s" % suffix,
                    "code": "CM-%s" % suffix,
                    "lang": "en_US",
                    "gradebook_id": gradebook.id,
                }
            )
            subject = setup_env["op.subject"].create(
                {
                    "name": "Concurrent subject %s" % suffix,
                    "code": "CMS-%s" % suffix,
                    "course_id": course.id,
                    "gradebook_id": gradebook.id,
                }
            )
            product = setup_env["product.product"].create(
                {"name": "Concurrent fee %s" % suffix, "type": "service"}
            )
            register = setup_env["op.admission.register"].create(
                {
                    "name": "Concurrent register %s" % suffix,
                    "course_id": course.id,
                    "product_id": product.id,
                    "start_date": date(2026, 1, 1),
                    "end_date": date(2026, 12, 31),
                    "min_count": 1,
                    "max_count": 2,
                }
            )
            partner = setup_env["res.partner"].with_context(
                skip_moodle_sync=True
            ).create(
                {
                    "name": "Concurrent Student %s" % suffix,
                    "email": "concurrent-%s@example.com" % suffix,
                    "username": "concurrent-%s" % suffix,
                }
            )
            student = setup_env["op.student"].create(
                {
                    "first_name": "Concurrent",
                    "last_name": suffix,
                    "gender": "o",
                    "partner_id": partner.id,
                }
            )
            batch = setup_env["op.batch"].create(
                {
                    "name": "Concurrent batch %s" % suffix,
                    "code": "CMB-%s" % suffix,
                    "course_id": course.id,
                    "start_date": date(2026, 1, 1),
                    "end_date": date(2026, 12, 31),
                }
            )
            admission = setup_env["op.admission"].with_context(
                skip_moodle_sync=True
            ).create(
                {
                    "name": "Concurrent Student %s" % suffix,
                    "first_name": "Concurrent",
                    "last_name": suffix,
                    "birth_date": date(1990, 1, 1),
                    "gender": "o",
                    "email": partner.email,
                    "student_id": student.id,
                    "course_id": course.id,
                    "batch_id": batch.id,
                    "register_id": register.id,
                    "partner_id": partner.id,
                    "admission_date": date(2026, 1, 1),
                }
            )
            gradebook_student = setup_env["app.gradebook.student"].create(
                {"admission_id": admission.id}
            )
            gradebook_subject = setup_env["app.gradebook.subject"].create(
                {
                    "gradebook_student_id": gradebook_student.id,
                    "op_subject_id": subject.id,
                }
            )
            wizards = setup_env["irg.gradebook.moodle.sync.wizard"].create(
                [
                    {"gradebook_student_id": gradebook_student.id},
                    {"gradebook_student_id": gradebook_student.id},
                ]
            )
            for wizard in wizards:
                setup_env["irg.gradebook.moodle.sync.wizard.line"].create(
                    {
                        "wizard_id": wizard.id,
                        "gradebook_subject_id": gradebook_subject.id,
                        "subject_id": subject.id,
                        "survey_type": "exam",
                        "state": "ok",
                        "apply_line": True,
                        "grade_to_apply": 8.0,
                        "graded_count": 1,
                    }
                )
            setup = {
                "uid": setup_env.uid,
                "wizard_ids": wizards.ids,
                "gradebook_subject_id": gradebook_subject.id,
                "gradebook_student_id": gradebook_student.id,
                "admission_id": admission.id,
                "student_id": student.id,
                "partner_id": partner.id,
                "batch_id": batch.id,
                "register_id": register.id,
                "product_id": product.id,
                "subject_id": subject.id,
                "course_id": course.id,
                "gradebook_id": gradebook.id,
            }
            setup_cr.commit()
        return setup

    def _cleanup_committed_concurrency_case(self, setup):
        with self.env.registry.cursor() as cleanup_cr:
            cleanup_env = api.Environment(cleanup_cr, setup["uid"], {})
            cleanup_env["app.gradebook.result"].search(
                [("gradebook_subject_id", "=", setup["gradebook_subject_id"])]
            ).unlink()
            cleanup_env["irg.gradebook.moodle.sync.wizard"].browse(
                setup["wizard_ids"]
            ).unlink()
            cleanup_env["app.gradebook.student"].browse(
                setup["gradebook_student_id"]
            ).unlink()
            cleanup_env["op.admission"].browse(setup["admission_id"]).unlink()
            cleanup_env["op.student"].browse(setup["student_id"]).unlink()
            cleanup_env["res.partner"].browse(setup["partner_id"]).unlink()
            cleanup_env["op.batch"].browse(setup["batch_id"]).unlink()
            cleanup_env["op.admission.register"].browse(
                setup["register_id"]
            ).unlink()
            cleanup_env["product.product"].browse(setup["product_id"]).unlink()
            cleanup_env["op.subject"].browse(setup["subject_id"]).unlink()
            cleanup_env["op.course"].browse(setup["course_id"]).unlink()
            cleanup_env["app.gradebook"].browse(setup["gradebook_id"]).unlink()
            cleanup_cr.commit()
        with self.env.registry.cursor() as verify_cr:
            verify_env = api.Environment(verify_cr, setup["uid"], {})
            self.assertFalse(
                verify_env["app.gradebook"].search_count(
                    [("id", "=", setup["gradebook_id"])]
                )
            )
            self.assertFalse(
                verify_env["res.partner"].search_count(
                    [("id", "=", setup["partner_id"])]
                )
            )

    def test_concurrent_apply_retries_and_keeps_one_result(self):
        """Dos transacciones serializan el upsert y terminan con una sola fila."""
        setup = self._create_committed_concurrency_case()
        self.addCleanup(self._cleanup_committed_concurrency_case, setup)
        lock_acquired = threading.Event()
        release_first = threading.Event()
        second_attempted = threading.Event()
        thread_context = threading.local()
        errors = []
        attempts = [0, 0]
        model_class = type(self.env["irg.gradebook.moodle.sync.wizard"])
        original_lock = model_class._lock_apply_subjects

        def coordinated_lock(wizard, subject_ids):
            if thread_context.worker == 1:
                second_attempted.set()
            result = original_lock(wizard, subject_ids)
            if thread_context.worker == 0 and attempts[0] == 1:
                lock_acquired.set()
                if not release_first.wait(5):
                    raise AssertionError("timeout releasing first apply")
            return result

        def apply(worker_index):
            thread_context.worker = worker_index
            try:
                with self.env.registry.cursor() as worker_cr:
                    worker_env = api.Environment(worker_cr, setup["uid"], {})

                    def request():
                        attempts[worker_index] += 1
                        worker_cr.execute("SET LOCAL statement_timeout = '10s'")
                        return worker_env[
                            "irg.gradebook.moodle.sync.wizard"
                        ].browse(setup["wizard_ids"][worker_index]).action_apply()

                    service_model.retrying(request, worker_env)
                    worker_cr.commit()
            except Exception as error:  # asserted in parent thread
                errors.append(error)

        first = threading.Thread(target=apply, args=(0,))
        second = threading.Thread(target=apply, args=(1,))
        try:
            with patch.object(model_class, "_lock_apply_subjects", coordinated_lock):
                first.start()
                self.assertTrue(lock_acquired.wait(5))
                second.start()
                self.assertTrue(second_attempted.wait(5))
                release_first.set()
                first.join(10)
                second.join(10)
            self.assertFalse(first.is_alive())
            self.assertFalse(second.is_alive())
            self.assertFalse(errors)
            self.assertGreaterEqual(attempts[1], 2)
            with self.env.registry.cursor() as assert_cr:
                assert_env = api.Environment(assert_cr, setup["uid"], {})
                self.assertEqual(
                    assert_env["app.gradebook.result"].search_count(
                        [
                            (
                                "gradebook_subject_id",
                                "=",
                                setup["gradebook_subject_id"],
                            ),
                            ("is_moodle", "=", True),
                            ("survey_type", "=", "exam"),
                        ]
                    ),
                    1,
                )
        finally:
            release_first.set()
            if first.is_alive():
                first.join(10)
            if second.is_alive():
                second.join(10)

    def test_stale_wizard_line_raises_serialization_failure(self):
        """Una edición concurrente del transient invalida el snapshot lector."""
        setup = self._create_committed_concurrency_case()
        self.addCleanup(self._cleanup_committed_concurrency_case, setup)

        with self.env.registry.cursor() as stale_cr:
            stale_env = api.Environment(stale_cr, setup["uid"], {})
            stale_wizard = stale_env[
                "irg.gradebook.moodle.sync.wizard"
            ].browse(setup["wizard_ids"][0])
            stale_line = stale_wizard.line_ids
            self.assertEqual(stale_line.grade_to_apply, 8.0)

            with self.env.registry.cursor() as editor_cr:
                editor_env = api.Environment(editor_cr, setup["uid"], {})
                editor_env["irg.gradebook.moodle.sync.wizard.line"].browse(
                    stale_line.id
                ).write({"grade_to_apply": 9.0})
                editor_cr.commit()

            with self.assertRaises(SerializationFailure):
                stale_wizard.action_apply()

        with self.env.registry.cursor() as assert_cr:
            assert_env = api.Environment(assert_cr, setup["uid"], {})
            self.assertFalse(
                assert_env["app.gradebook.result"].search(
                    [
                        (
                            "gradebook_subject_id",
                            "=",
                            setup["gradebook_subject_id"],
                        ),
                        ("is_moodle", "=", True),
                    ]
                )
            )
