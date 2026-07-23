import base64
import csv
import io
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged

from ..services.mapping_import import MAX_FILE_SIZE, MappingImportService
from .common import MappingAdminCommon


MAX_BASE64_SIZE = 4 * ((MAX_FILE_SIZE + 2) // 3)
COURSE_FIELDS = [
    "Moodle Course ID",
    "Odoo Course Name",
    "Odoo Course ID",
    "Nombre del Curso",
]
ASSIGNMENT_FIELDS = [
    "Curso Nombre",
    "Odoo Course ID",
    "Moodle Course ID",
    "Odoo Subject Name",
    "Odoo Subject ID",
    "Odoo Subject Code",
    "Moodle IDs List",
    "Moodle Names Found",
]


@tagged("post_install", "-at_install")
class TestMappingImportWizard(MappingAdminCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env["irg.gradebook.moodle.mapping.import.wizard"]
        cls.internal_user = cls.env["res.users"].with_context(
            no_reset_password=True
        ).create(
            {
                "name": "Operador importación Moodle",
                "login": "mapping-import-operator-tests",
                "email": "mapping-import-operator@example.com",
                "groups_id": [
                    Command.set([cls.env.ref("base.group_user").id])
                ],
            }
        )

    @staticmethod
    def _csv_payload(fieldnames, rows):
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            delimiter=";",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)
        return stream.getvalue().encode("utf-8-sig")

    def _uploads(self, moodle_course_id=460001, activity_id=560001):
        moodle_name = "Curso Test Mapping Admin (ONLINE 2026)"
        courses = self._csv_payload(
            COURSE_FIELDS,
            [
                {
                    "Moodle Course ID": str(moodle_course_id),
                    "Odoo Course Name": self.course.name,
                    "Odoo Course ID": str(self.course.id),
                    "Nombre del Curso": moodle_name,
                }
            ],
        )
        assignments = self._csv_payload(
            ASSIGNMENT_FIELDS,
            [
                {
                    "Curso Nombre": moodle_name,
                    "Odoo Course ID": str(self.course.id),
                    "Moodle Course ID": str(moodle_course_id),
                    "Odoo Subject Name": self.subject.name,
                    "Odoo Subject ID": str(self.subject.id),
                    "Odoo Subject Code": self.subject.code,
                    "Moodle IDs List": str(activity_id),
                    "Moodle Names Found": "Actividad importada",
                }
            ],
        )
        return base64.b64encode(courses), base64.b64encode(assignments)

    def _wizard(self, moodle_course_id=460001, activity_id=560001):
        courses, assignments = self._uploads(moodle_course_id, activity_id)
        return self.Wizard.create(
            {
                "courses_file": courses,
                "courses_filename": "mapeo cursos.csv",
                "assignments_file": assignments,
                "assignments_filename": "Mapeo asignaturas.csv",
            }
        )

    def _persistent_mapping_snapshot(self):
        model_fields = {
            "irg.gradebook.moodle.course.map": [
                "id",
                "op_course_id",
                "moodle_course_id",
                "moodle_course_name",
                "modality",
                "edition_year",
                "active",
                "write_uid",
                "write_date",
            ],
            "irg.gradebook.moodle.map": [
                "id",
                "op_subject_id",
                "moodle_course_id",
                "moodle_course_name",
                "course_map_id",
                "active",
                "write_uid",
                "write_date",
            ],
            "irg.gradebook.moodle.map.line": [
                "id",
                "map_id",
                "moodle_activity_id",
                "name",
                "activity_type",
                "write_uid",
                "write_date",
            ],
        }
        return {
            model_name: self.env[model_name]
            .with_context(active_test=False)
            .search([], order="id")
            .read(field_names)
            for model_name, field_names in model_fields.items()
        }

    def test_non_admin_cannot_create_write_or_call_public_actions(self):
        courses, assignments = self._uploads()
        with self.assertRaises(AccessError):
            self.Wizard.with_user(self.internal_user).create(
                {
                    "courses_file": courses,
                    "assignments_file": assignments,
                }
            )

        wizard = self._wizard()
        restricted = wizard.with_user(self.internal_user)
        with self.assertRaises(AccessError):
            restricted.write({"courses_filename": "otro.csv"})
        for action_name in (
            "action_validate",
            "action_apply",
            "action_open_course_maps",
            "action_open_subject_maps",
        ):
            with self.subTest(action=action_name), self.assertRaises(AccessError):
                getattr(restricted, action_name)()

    def test_decode_rejects_missing_invalid_and_unexpected_types(self):
        for value in (False, None, b""):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.Wizard._decode_upload(value, "mapeo cursos.csv")
        with self.assertRaises(ValidationError):
            self.Wizard._decode_upload(b"base64!!", "mapeo cursos.csv")
        for value in (123, bytearray(b"YWJj"), {"payload": "YWJj"}):
            with self.subTest(value_type=type(value).__name__), self.assertRaises(
                ValidationError
            ):
                self.Wizard._check_encoded_upload(value, "mapeo cursos.csv")

    def test_decode_accepts_exact_limit_and_rejects_one_decoded_byte_over(self):
        exact_payload = b"a" * MAX_FILE_SIZE
        exact_encoded = base64.b64encode(exact_payload)
        self.assertEqual(len(exact_encoded), MAX_BASE64_SIZE)
        self.assertEqual(
            self.Wizard._decode_upload(exact_encoded, "mapeo cursos.csv"),
            exact_payload,
        )

        oversized_encoded = base64.b64encode(exact_payload + b"a")
        self.assertEqual(len(oversized_encoded), MAX_BASE64_SIZE)
        with self.assertRaises(ValidationError):
            self.Wizard._decode_upload(oversized_encoded, "mapeo cursos.csv")

    def test_encoded_limit_runs_before_decoder_and_rpc_persistence(self):
        encoded = b"A" * (MAX_BASE64_SIZE + 1)
        with patch(
            "odoo.addons.irg_gradebook_moodle_mapping_admin.wizard."
            "mapping_import_wizard.base64.b64decode"
        ) as decoder, self.assertRaises(ValidationError):
            self.Wizard._decode_upload(encoded, "mapeo cursos.csv")
        decoder.assert_not_called()

        with self.assertRaises(ValidationError):
            self.Wizard.create({"courses_file": encoded})
        wizard = self._wizard()
        with self.assertRaises(ValidationError):
            wizard.write({"assignments_file": encoded})

    def test_validate_is_read_only_and_summary_is_deterministic(self):
        wizard = self._wizard()
        before = self._persistent_mapping_snapshot()

        with patch.object(
            MappingImportService, "apply_plan", autospec=True
        ) as apply_plan, patch.object(
            MappingImportService, "_upsert_course", autospec=True
        ) as upsert_course, patch.object(
            MappingImportService, "_upsert_subject", autospec=True
        ) as upsert_subject, patch.object(
            MappingImportService, "_upsert_activities", autospec=True
        ) as upsert_activities:
            wizard.action_validate()

        self.assertEqual(wizard.state, "validated")
        self.assertEqual(
            wizard.summary_text,
            "Cursos: leídas 1; válidas 1; omitidas 0; advertidas 0.\n"
            "Asignaturas: leídas 1; válidas 1; omitidas 0; advertidas 0.\n"
            "Mapas de curso: se crearán 1; se actualizarán 0.\n"
            "Mapas de asignatura: se crearán 1; se actualizarán 0.\n"
            "Actividades: se crearán 1; se actualizarán 0.",
        )
        apply_plan.assert_not_called()
        upsert_course.assert_not_called()
        upsert_subject.assert_not_called()
        upsert_activities.assert_not_called()
        self.assertEqual(self._persistent_mapping_snapshot(), before)

    def test_summary_translates_fixed_reason_keys_to_spanish_labels(self):
        courses, assignments = self._uploads(
            moodle_course_id=460006, activity_id=560006
        )
        decoded_courses = base64.b64decode(courses).decode("utf-8-sig")
        decoded_assignments = base64.b64decode(assignments).decode("utf-8-sig")
        courses = base64.b64encode((decoded_courses + ";;;\n").encode("utf-8-sig"))
        assignments = base64.b64encode(
            (
                decoded_assignments.replace(
                    "560006;Actividad importada",
                    "560006, 560006;Actividad importada",
                )
                + "%s;%s;%s;%s;%s;%s;;\n"
                % (
                    "Curso Test Mapping Admin (ONLINE 2026)",
                    self.course.id,
                    460006,
                    self.subject.name,
                    self.subject.id,
                    self.subject.code,
                )
            ).encode("utf-8-sig")
        )
        wizard = self.Wizard.create(
            {"courses_file": courses, "assignments_file": assignments}
        )

        wizard.action_validate()

        self.assertIn("fila vacía=1", wizard.summary_text)
        self.assertIn("sin identificadores de actividad=1", wizard.summary_text)
        self.assertIn("identificador de actividad duplicado=1", wizard.summary_text)
        self.assertIn(
            "cantidad de nombres de actividad distinta de los identificadores=1",
            wizard.summary_text,
        )
        for internal_reason in (
            "blank_row",
            "no_activity_ids",
            "duplicate_activity_id",
            "activity_name_count_mismatch",
        ):
            self.assertNotIn(internal_reason, wizard.summary_text)

        empty_stats = {
            "rows_read": 0,
            "rows_accepted": 0,
            "rows_skipped": 0,
            "rows_warned": 0,
            "skipped_by_reason": {},
            "warned_by_reason": {},
        }
        unknown_reason = "future_private_reason_with_row_value"
        course_stats = dict(
            empty_stats,
            rows_read=1,
            rows_skipped=1,
            skipped_by_reason={unknown_reason: 1},
        )
        fallback_summary = self.Wizard._format_summary(
            {"courses": course_stats, "assignments": empty_stats}
        )
        self.assertIn("otro motivo de validación=1", fallback_summary)
        self.assertNotIn(unknown_reason, fallback_summary)

    def test_service_errors_are_fixed_spanish_messages_without_source_echo(self):
        bad_courses = base64.b64encode(b"cabecera incorrecta\nvalor\n")
        assignments = self._uploads(moodle_course_id=460007)[1]
        wizard = self.Wizard.create(
            {
                "courses_file": bad_courses,
                "assignments_file": assignments,
            }
        )

        with self.assertRaisesRegex(
            ValidationError,
            "El CSV de cursos no contiene todas las cabeceras obligatorias",
        ) as known_error:
            wizard.action_validate()
        self.assertNotIn("missing required header", str(known_error.exception))
        self.assertNotIn("CSV courses", str(known_error.exception))

        secret_error = "English parser failure: fila con Persona Privada"
        with patch.object(
            MappingImportService,
            "analyze_bytes",
            side_effect=ValueError(secret_error),
        ), self.assertRaisesRegex(
            ValidationError,
            "No se pudieron analizar los archivos CSV",
        ) as unknown_error:
            wizard.action_validate()
        self.assertNotIn(secret_error, str(unknown_error.exception))
        self.assertIsNone(unknown_error.exception.__cause__)
        self.assertTrue(unknown_error.exception.__suppress_context__)

    def test_missing_file_and_action_state_guards_are_server_side(self):
        wizard = self._wizard()
        wizard.write({"courses_file": False})
        with self.assertRaises(ValidationError):
            wizard.action_validate()

        wizard = self._wizard(moodle_course_id=460002)
        with self.assertRaises(ValidationError):
            wizard.action_apply()
        with self.assertRaises(ValidationError):
            wizard.action_open_course_maps()
        with self.assertRaises(ValidationError):
            wizard.action_open_subject_maps()
        wizard.action_validate()
        with self.assertRaises(ValidationError):
            wizard.action_validate()

        other = self._wizard(moodle_course_id=460003)
        with self.assertRaises(ValueError):
            (wizard | other).action_apply()

    def test_file_change_resets_validation_and_server_owned_results(self):
        wizard = self._wizard()
        wizard.action_validate()
        wizard.write(
            {
                "assignments_file": self._uploads(activity_id=560002)[1],
                "state": "applied",
                "summary_text": "contenido cliente",
                "affected_course_map_ids": [Command.set([self.course_map.id])],
                "affected_subject_map_ids": [Command.set([self.subject_map.id])],
            }
        )

        self.assertEqual(wizard.state, "draft")
        self.assertFalse(wizard.summary_text)
        self.assertFalse(wizard.affected_course_map_ids)
        self.assertFalse(wizard.affected_subject_map_ids)

    def test_apply_reanalyzes_persisted_bytes_and_records_affected_maps(self):
        wizard = self._wizard(moodle_course_id=460004, activity_id=560004)
        wizard.action_validate()
        expected_courses = base64.b64decode(wizard.courses_file)
        expected_assignments = base64.b64decode(wizard.assignments_file)

        with patch.object(
            MappingImportService,
            "analyze_bytes",
            wraps=MappingImportService(self.env).analyze_bytes,
        ) as analyze:
            wizard.action_apply()

        analyze.assert_called_once_with(expected_courses, expected_assignments)
        self.assertEqual(wizard.state, "applied")
        self.assertEqual(len(wizard.affected_course_map_ids), 1)
        self.assertEqual(len(wizard.affected_subject_map_ids), 1)
        self.assertIn("Mapas de curso: creados 1; actualizados 0.", wizard.summary_text)
        self.assertIn(
            "Mapas de asignatura: creados 1; actualizados 0.",
            wizard.summary_text,
        )
        self.assertIn("Actividades: creadas 1; actualizadas 0.", wizard.summary_text)

    def test_open_actions_are_filtered_to_applied_records(self):
        wizard = self._wizard(moodle_course_id=460005, activity_id=560005)
        wizard.action_validate()
        wizard.action_apply()

        course_action = wizard.action_open_course_maps()
        subject_action = wizard.action_open_subject_maps()

        self.assertEqual(course_action["res_model"], "irg.gradebook.moodle.course.map")
        self.assertEqual(
            course_action["domain"],
            [("id", "in", wizard.affected_course_map_ids.ids)],
        )
        self.assertEqual(subject_action["res_model"], "irg.gradebook.moodle.map")
        self.assertEqual(
            subject_action["domain"],
            [("id", "in", wizard.affected_subject_map_ids.ids)],
        )

    def test_acl_actions_menu_and_inherited_views_are_system_only(self):
        model = self.env["ir.model"]._get(
            "irg.gradebook.moodle.mapping.import.wizard"
        )
        access = self.env["ir.model.access"].search(
            [("model_id", "=", model.id)]
        )
        self.assertEqual(len(access), 1)
        self.assertEqual(access.group_id, self.env.ref("base.group_system"))
        self.assertTrue(
            all(
                (
                    access.perm_read,
                    access.perm_write,
                    access.perm_create,
                    access.perm_unlink,
                )
            )
        )

        action = self.env.ref(
            "irg_gradebook_moodle_mapping_admin."
            "action_irg_gradebook_moodle_mapping_import"
        )
        menu = self.env.ref(
            "irg_gradebook_moodle_mapping_admin."
            "menu_irg_gradebook_moodle_mapping_import"
        )
        self.assertEqual(action.groups_id, self.env.ref("base.group_system"))
        self.assertEqual(menu.groups_id, self.env.ref("base.group_system"))

        expected_fields = {
            "irg_op_course_database_id",
            "irg_subject_map_count",
            "irg_subject_map_ids",
            "irg_op_course_id",
            "irg_op_subject_database_id",
            "irg_op_subject_name",
            "irg_op_subject_code",
            "irg_activity_count",
            "irg_activity_ids_display",
        }
        view_xmlids = (
            "irg_gradebook_moodle_course_map_tree_admin",
            "irg_gradebook_moodle_course_map_form_admin",
            "irg_gradebook_moodle_map_tree_admin",
            "irg_gradebook_moodle_map_form_admin",
        )
        combined_arch = "".join(
            self.env.ref(
                "irg_gradebook_moodle_mapping_admin.%s" % xmlid
            ).arch_db
            for xmlid in view_xmlids
        )
        for field_name in expected_fields:
            self.assertIn('name="%s"' % field_name, combined_arch)
        flat_subject_tree = self.env.ref(
            "irg_gradebook_moodle_mapping_admin."
            "irg_gradebook_moodle_map_tree_admin"
        ).arch_db
        self.assertIn('name="active"', flat_subject_tree)
