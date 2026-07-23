import csv
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from psycopg2 import IntegrityError

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from odoo.addons.irg_gradebook_moodle_routing.tools.import_moodle_routing_csv import (
    run_import,
)
from odoo.addons.irg_gradebook_moodle_wizard.wizard.moodle_sync_wizard import (
    IrgGradebookMoodleSyncWizard as BaseMoodleSyncWizard,
)


@tagged("post_install", "-at_install")
class TestMoodleRouting(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gradebook = cls.env["app.gradebook"].create(
            {
                "name": "Plantilla Test Routing Moodle",
                "grading_scale": 10,
                "gradebook_template_ids": [
                    Command.create({"type": "exam", "weight": 100, "qty": 1})
                ],
            }
        )
        cls.course = cls.env["op.course"].create(
            {
                "name": "Curso Test Routing Moodle",
                "code": "CTR-MOODLE",
                "lang": "en_US",
                "gradebook_id": cls.gradebook.id,
            }
        )
        cls.subject = cls.env["op.subject"].create(
            {
                "name": "Asignatura Test Routing Moodle",
                "code": "ATR-MOODLE",
                "course_id": cls.course.id,
                "gradebook_id": cls.gradebook.id,
            }
        )
        cls.course.write({"subject_ids": [Command.link(cls.subject.id)]})
        cls.product = cls.env["product.product"].create(
            {"name": "Routing Moodle Fee", "type": "service"}
        )
        cls.register = cls.env["op.admission.register"].create(
            {
                "name": "Routing Moodle Register",
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
                "name": "Alumno Routing Moodle",
                "email": "routing.moodle@example.com",
                "username": "routing.moodle",
                "md_id": 770001,
            }
        )
        cls.student = cls.env["op.student"].create(
            {
                "first_name": "Alumno",
                "last_name": "Routing Moodle",
                "gender": "o",
                "partner_id": cls.partner.id,
            }
        )
        cls.batch = cls.env["op.batch"].create(
            {
                "name": "Batch Routing Moodle",
                "code": "ROUTE-HC",
                "course_id": cls.course.id,
                "start_date": date(2026, 1, 1),
                "end_date": date(2026, 12, 31),
            }
        )
        cls.admission = cls.env["op.admission"].with_context(
            skip_moodle_sync=True
        ).create(
            {
                "name": "Alumno Routing Moodle",
                "first_name": "Alumno",
                "last_name": "Routing Moodle",
                "birth_date": date(1990, 1, 1),
                "gender": "o",
                "email": "routing.moodle@example.com",
                "student_id": cls.student.id,
                "course_id": cls.course.id,
                "batch_id": cls.batch.id,
                "register_id": cls.register.id,
                "partner_id": cls.partner.id,
                "admission_date": date(2026, 1, 1),
            }
        )
        cls.gradebook_student = cls.env["app.gradebook.student"].create(
            {"admission_id": cls.admission.id}
        )

    def _course_map(self, name, moodle_course_id):
        return self.env["irg.gradebook.moodle.course.map"].create(
            {
                "op_course_id": self.course.id,
                "moodle_course_id": moodle_course_id,
                "moodle_course_name": name,
            }
        )

    def _wizard(self):
        return self.env["irg.gradebook.moodle.sync.wizard"].create(
            {"gradebook_student_id": self.gradebook_student.id}
        )

    def test_course_name_classification_and_year(self):
        cases = (
            ("Máster HomeClass", "homeclass", False),
            ("Máster (ONLINE)", "online", False),
            ("Máster (ONLINE 2026)", "online", 2026),
            ("Máster (online 2027)", "online", 2027),
        )
        for index, (name, modality, edition_year) in enumerate(cases, 1):
            with self.subTest(name=name):
                mapping = self._course_map(name, 810000 + index)
                self.assertEqual(mapping.modality, modality)
                self.assertEqual(mapping.edition_year, edition_year)

        empty = self.env["irg.gradebook.moodle.course.map"].new(
            {"moodle_course_name": False}
        )
        empty._compute_routing_metadata()
        self.assertFalse(empty.modality)
        self.assertFalse(empty.edition_year)

    def test_malformed_online_markers_are_not_selectable(self):
        malformed_names = (
            "Curso (ONLINE2026)",
            "Curso (online 26)",
            "Curso (OnLiNe 2026 EXTRA)",
        )
        for index, name in enumerate(malformed_names, 1):
            with self.subTest(name=name):
                mapping = self._course_map(name, 810100 + index)
                self.assertFalse(mapping.modality)
                self.assertFalse(mapping.edition_year)

    def test_course_map_constraints_and_fields(self):
        model = self.env["irg.gradebook.moodle.course.map"]
        self.assertTrue(model._fields["op_course_id"].required)
        self.assertEqual(model._fields["op_course_id"].ondelete, "restrict")
        self.assertTrue(model._fields["moodle_course_id"].index)
        self.assertTrue(model._fields["moodle_course_name"].required)
        self.assertTrue(model._fields["modality"].store)
        self.assertTrue(model._fields["edition_year"].readonly)
        first = self._course_map("Curso HC", 810010)
        with self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self._course_map("Curso HC duplicado", first.moodle_course_id).flush_recordset()
        with self.assertRaises(IntegrityError), self.env.cr.savepoint():
            self._course_map("Curso inválido", 0).flush_recordset()

    def test_subject_map_rejects_mismatched_parent_integrity(self):
        parent = self._course_map("Curso HomeClass", 810011)
        with self.assertRaises(ValidationError):
            self.env["irg.gradebook.moodle.map"].create(
                {
                    "op_subject_id": self.subject.id,
                    "moodle_course_id": 810012,
                    "course_map_id": parent.id,
                }
            )

        other_course = self.env["op.course"].create(
            {"name": "Curso padre ajeno", "code": "PARENT-OTHER", "lang": "en_US"}
        )
        other_parent = self.env["irg.gradebook.moodle.course.map"].create(
            {
                "op_course_id": other_course.id,
                "moodle_course_id": 810013,
                "moodle_course_name": "Curso padre ajeno HomeClass",
            }
        )
        with self.assertRaises(ValidationError):
            self.env["irg.gradebook.moodle.map"].create(
                {
                    "op_subject_id": self.subject.id,
                    "moodle_course_id": other_parent.moodle_course_id,
                    "course_map_id": other_parent.id,
                }
            )

    def test_course_map_rejects_parent_edits_that_corrupt_children(self):
        moodle_parent = self._course_map("Curso HomeClass Moodle", 810014)
        self.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": self.subject.id,
                "moodle_course_id": moodle_parent.moodle_course_id,
                "course_map_id": moodle_parent.id,
            }
        )
        with self.assertRaises(ValidationError):
            moodle_parent.moodle_course_id = 810015

        other_course = self.env["op.course"].create(
            {"name": "Curso padre editado", "code": "PARENT-EDIT", "lang": "en_US"}
        )
        course_parent = self._course_map("Curso HomeClass Odoo", 810016)
        self.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": self.subject.id,
                "moodle_course_id": course_parent.moodle_course_id,
                "course_map_id": course_parent.id,
            }
        )
        with self.assertRaises(ValidationError):
            course_parent.op_course_id = other_course

    def test_routing_homeclass_and_online_year(self):
        homeclass = self._course_map("Curso HomeClass", 810020)
        online_generic = self._course_map("Curso (ONLINE)", 810021)
        online_2026 = self._course_map("Curso (ONLINE 2026)", 810022)
        wizard = self._wizard()

        self.batch.code = "PROMO-HC"
        self.assertEqual(wizard._irg_resolve_course_map(), homeclass)
        self.batch.code = "PROMO-ONL"
        self.assertEqual(wizard._irg_resolve_course_map(), online_2026)
        online_2026.active = False
        self.assertEqual(wizard._irg_resolve_course_map(), online_generic)

    def test_routing_rejects_missing_ambiguous_or_unknown_selection(self):
        wizard = self._wizard()
        for batch_code in ("SIN-MODALIDAD", "HC-ONL"):
            with self.subTest(batch_code=batch_code):
                self.batch.code = batch_code
                with self.assertRaises(UserError):
                    wizard._irg_resolve_course_map()

        self.batch.code = "SOLO-HC"
        with self.assertRaises(UserError):
            wizard._irg_resolve_course_map()
        self._course_map("Curso HC A", 810030)
        self._course_map("Curso HC B", 810031)
        with self.assertRaises(UserError):
            wizard._irg_resolve_course_map()

    def test_routing_failure_happens_before_moodle_service(self):
        self.batch.code = "AMBIGUO-HC-ONL"
        wizard = self._wizard()
        with patch.object(BaseMoodleSyncWizard, "_get_service") as get_service:
            with self.assertRaises(UserError):
                wizard.action_load_moodle_data()
        get_service.assert_not_called()

    def test_corrupt_historical_subject_map_blocks_before_moodle_service(self):
        parent = self._course_map("Curso HomeClass", 810035)
        subject_map = self.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": self.subject.id,
                "moodle_course_id": parent.moodle_course_id,
                "course_map_id": parent.id,
            }
        )
        self.env.cr.execute(
            "UPDATE irg_gradebook_moodle_map SET moodle_course_id = %s WHERE id = %s",
            (810036, subject_map.id),
        )
        subject_map.invalidate_recordset(["moodle_course_id"])
        self.batch.code = "HISTORICO-HC"

        with patch.object(BaseMoodleSyncWizard, "_get_service") as get_service:
            with self.assertRaisesRegex(UserError, "incoherente"):
                self._wizard().action_load_moodle_data()
        get_service.assert_not_called()

    def test_malformed_online_map_blocks_before_moodle_service(self):
        self._course_map("Curso (ONLINE2026)", 810037)
        self.batch.code = "MALFORMADO-ONL"
        with patch.object(BaseMoodleSyncWizard, "_get_service") as get_service:
            with self.assertRaisesRegex(UserError, "online genérico"):
                self._wizard().action_load_moodle_data()
        get_service.assert_not_called()

    def test_routing_preserves_server_side_access_guard(self):
        internal_user = self.env["res.users"].with_context(
            no_reset_password=True
        ).create(
            {
                "name": "Usuario Interno Routing Moodle",
                "login": "internal-routing-moodle",
                "email": "internal-routing-moodle@example.com",
                "groups_id": [Command.set([self.env.ref("base.group_user").id])],
            }
        )
        self.batch.code = "AMBIGUO-HC-ONL"
        with self.assertRaisesRegex(AccessError, "No tiene permisos"):
            self._wizard().with_user(internal_user).action_load_moodle_data()

    def test_selected_parent_filters_subject_maps_and_is_forwarded(self):
        selected = self._course_map("Curso HomeClass", 810040)
        other = self._course_map("Otro HomeClass", 810041)
        selected_subject_map = self.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": self.subject.id,
                "moodle_course_id": selected.moodle_course_id,
                "course_map_id": selected.id,
            }
        )
        self.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": self.subject.id,
                "moodle_course_id": other.moodle_course_id,
                "course_map_id": other.id,
            }
        )
        filtered = self.env["irg.gradebook.moodle.map"].with_context(
            irg_gradebook_moodle_course_map_id=selected.id
        ).search([("op_subject_id", "=", self.subject.id)])
        self.assertEqual(filtered, selected_subject_map)
        other.active = False

        observed = {}

        def capture_context(base_self):
            observed["course_map_id"] = base_self.env.context.get(
                "irg_gradebook_moodle_course_map_id"
            )
            return True

        wizard = self._wizard()
        with patch.object(
            BaseMoodleSyncWizard,
            "action_load_moodle_data",
            new=capture_context,
        ):
            self.assertTrue(wizard.action_load_moodle_data())
        self.assertEqual(observed["course_map_id"], selected.id)

    @staticmethod
    def _write_csv(path, fieldnames, rows):
        with path.open("w", newline="", encoding="mac_roman") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=fieldnames,
                delimiter=";",
                extrasaction="ignore",
            )
            writer.writeheader()
            writer.writerows(rows)

    def _run_import(
        self,
        home_rows,
        online_rows,
        assignment_rows,
        home_fields=None,
        online_fields=None,
        assignment_fields=None,
    ):
        with TemporaryDirectory() as directory:
            directory = Path(directory)
            home_path = directory / "homeclass.csv"
            online_path = directory / "online.csv"
            assignments_path = directory / "assignments.csv"
            self._write_csv(
                home_path,
                home_fields
                or ["Odoo Subject Name", "Odoo Subject ID", "Moodle IDs List"],
                home_rows,
            )
            self._write_csv(
                online_path,
                online_fields or ["Curso Moodle", "ID Curso", "ID Actividad"],
                online_rows,
            )
            self._write_csv(
                assignments_path,
                assignment_fields
                or [
                    "Curso Nombre",
                    "Odoo Course ID",
                    "Moodle Course ID",
                    "Odoo Subject Name",
                    "Odoo Subject ID",
                    "Moodle IDs List",
                    "Moodle Names Found",
                ],
                assignment_rows,
            )
            return run_import(
                self.env, home_path, online_path, assignments_path
            )

    def _assignment_row(self, **overrides):
        row = {
            "Curso Nombre": "Máster Psicología HomeClass",
            "Odoo Course ID": str(self.course.id),
            "Moodle Course ID": "35",
            "Odoo Subject Name": self.subject.name,
            "Odoo Subject ID": str(self.subject.id),
            "Moodle IDs List": "395, 397",
            "Moodle Names Found": "Prueba uno | Prueba dos",
        }
        row.update(overrides)
        return row

    def test_import_creates_and_is_idempotent(self):
        home_rows = [
            {
                "Odoo Subject Name": self.course.name,
                "Odoo Subject ID": str(self.course.id),
                "Moodle IDs List": "35",
            }
        ]
        rows = [self._assignment_row()]
        first = self._run_import(home_rows, [], rows)
        mapping = self.env["irg.gradebook.moodle.map"].search(
            [
                ("op_subject_id", "=", self.subject.id),
                ("moodle_course_id", "=", 35),
            ]
        )
        self.assertEqual(first["course_maps"]["created"], 1)
        self.assertEqual(first["subject_maps"]["created"], 1)
        self.assertEqual(mapping.course_map_id.op_course_id, self.course)
        self.assertEqual(mapping.course_map_id.moodle_course_name, rows[0]["Curso Nombre"])
        self.assertEqual(mapping.line_ids.mapped("moodle_activity_id"), [395, 397])

        line_ids = mapping.line_ids.ids
        second = self._run_import(home_rows, [], rows)
        self.assertEqual(second["course_maps"]["created"], 0)
        self.assertEqual(second["course_maps"]["updated"], 1)
        self.assertEqual(second["subject_maps"]["updated"], 1)
        self.assertEqual(mapping.line_ids.mapped("moodle_activity_id"), [395, 397])
        self.assertEqual(mapping.line_ids.ids, line_ids)

    def test_import_upserts_lines_without_deleting_or_losing_metadata(self):
        home_rows = [
            {
                "Odoo Subject Name": self.course.name,
                "Odoo Subject ID": str(self.course.id),
                "Moodle IDs List": "35",
            }
        ]
        first_row = self._assignment_row()
        self._run_import(home_rows, [], [first_row])
        mapping = self.env["irg.gradebook.moodle.map"].search(
            [
                ("op_subject_id", "=", self.subject.id),
                ("moodle_course_id", "=", 35),
            ]
        )
        retained = mapping.line_ids.filtered(
            lambda line: line.moodle_activity_id == 397
        )
        retained.write(
            {"name": "Nombre conservado", "activity_type": "assign"}
        )
        legacy = self.env["irg.gradebook.moodle.map.line"].create(
            {
                "map_id": mapping.id,
                "moodle_activity_id": 999,
                "name": "Actividad histórica",
                "activity_type": "assign",
            }
        )
        original_ids = {
            line.moodle_activity_id: line.id for line in mapping.line_ids
        }

        sparse_row = self._assignment_row(
            **{
                "Moodle IDs List": "395, 397, 398",
                "Moodle Names Found": "Nombre actualizado",
            }
        )
        self._run_import(home_rows, [], [sparse_row])
        lines = {
            line.moodle_activity_id: line for line in mapping.line_ids
        }
        self.assertEqual(set(lines), {395, 397, 398, 999})
        self.assertEqual(lines[395].id, original_ids[395])
        self.assertEqual(lines[397].id, original_ids[397])
        self.assertEqual(lines[397].name, "Nombre conservado")
        self.assertEqual(lines[397].activity_type, "assign")
        self.assertEqual(lines[398].name, False)
        self.assertEqual(lines[398].activity_type, "quiz")
        self.assertEqual(lines[999], legacy)

    def test_import_reports_each_source_and_invalid_authorizer_rows(self):
        home_rows = [
            {
                "Odoo Subject Name": self.course.name,
                "Odoo Subject ID": str(self.course.id),
                "Moodle IDs List": "35",
            },
            {
                "Odoo Subject Name": "Sin lista",
                "Odoo Subject ID": str(self.course.id),
                "Moodle IDs List": "",
            },
            {
                "Odoo Subject Name": "ID inválido",
                "Odoo Subject ID": "1.5",
                "Moodle IDs List": "36",
            },
        ]
        online_rows = [
            {"Curso Moodle": "Online válido", "ID Curso": "44", "ID Actividad": "395"},
            {"Curso Moodle": "Online cero", "ID Curso": "0", "ID Actividad": "396"},
            {"Curso Moodle": "Online decimal", "ID Curso": "44.5", "ID Actividad": "397"},
        ]
        assignments = [
            self._assignment_row(),
            self._assignment_row(**{"Moodle Course ID": "36"}),
        ]

        summary = self._run_import(home_rows, online_rows, assignments)
        self.assertEqual(
            summary["sources"],
            {
                "homeclass": {
                    "rows_read": 3,
                    "rows_accepted": 1,
                    "rows_discarded": 2,
                    "discarded_by_reason": {"invalid_values": 2},
                },
                "online": {
                    "rows_read": 3,
                    "rows_accepted": 1,
                    "rows_discarded": 2,
                    "discarded_by_reason": {"invalid_values": 2},
                },
                "assignments": {
                    "rows_read": 2,
                    "rows_accepted": 1,
                    "rows_discarded": 1,
                    "discarded_by_reason": {"unauthorized_course": 1},
                },
            },
        )

    def test_import_rejects_malformed_online_markers_with_specific_reason(self):
        online_rows = [
            {"Curso Moodle": "Online A", "ID Curso": "51", "ID Actividad": "395"},
            {"Curso Moodle": "Online B", "ID Curso": "52", "ID Actividad": "396"},
            {"Curso Moodle": "Online C", "ID Curso": "53", "ID Actividad": "397"},
        ]
        assignments = [
            self._assignment_row(
                **{
                    "Curso Nombre": name,
                    "Moodle Course ID": str(moodle_course_id),
                }
            )
            for name, moodle_course_id in (
                ("Curso (ONLINE2026)", 51),
                ("Curso (online 26)", 52),
                ("Curso (OnLiNe 2026 EXTRA)", 53),
            )
        ]

        summary = self._run_import([], online_rows, assignments)
        self.assertEqual(summary["skipped"], 3)
        self.assertEqual(
            summary["skipped_by_reason"],
            {"invalid_online_marker": 3},
        )
        self.assertEqual(
            summary["sources"]["assignments"],
            {
                "rows_read": 3,
                "rows_accepted": 0,
                "rows_discarded": 3,
                "discarded_by_reason": {"invalid_online_marker": 3},
            },
        )
        self.assertFalse(
            self.env["irg.gradebook.moodle.course.map"].search(
                [("moodle_course_id", "in", [51, 52, 53])]
            )
        )

    def test_import_rejects_missing_required_headers_explicitly(self):
        valid_home = [
            {
                "Odoo Subject ID": str(self.course.id),
                "Moodle IDs List": "35",
            }
        ]
        valid_online = [{"ID Curso": "44"}]
        assignments = [self._assignment_row()]
        cases = (
            {
                "label": "homeclass",
                "kwargs": {"home_fields": ["Odoo Subject ID"]},
                "missing": "Moodle IDs List",
            },
            {
                "label": "online",
                "kwargs": {"online_fields": ["Curso Moodle"]},
                "missing": "ID Curso",
            },
            {
                "label": "assignments",
                "kwargs": {
                    "assignment_fields": [
                        "Curso Nombre",
                        "Odoo Course ID",
                        "Moodle Course ID",
                        "Odoo Subject Name",
                        "Odoo Subject ID",
                        "Moodle IDs List",
                    ]
                },
                "missing": "Moodle Names Found",
            },
        )
        for case in cases:
            with self.subTest(source=case["label"]):
                with self.assertRaisesRegex(
                    ValueError,
                    "%s.*%s" % (case["label"], case["missing"]),
                ):
                    self._run_import(
                        valid_home,
                        valid_online,
                        assignments,
                        **case["kwargs"],
                    )

    def test_import_rejects_unauthorized_homeclass_36_and_online_inventory(self):
        home_rows = [
            {
                "Odoo Subject Name": self.course.name,
                "Odoo Subject ID": str(self.course.id),
                "Moodle IDs List": "35",
            }
        ]
        online_rows = [{"Curso Moodle": "Online", "ID Curso": "44", "ID Actividad": "395"}]
        rows = [
            self._assignment_row(**{"Moodle Course ID": "36"}),
            self._assignment_row(
                **{
                    "Curso Nombre": "Máster Psicología (ONLINE)",
                    "Moodle Course ID": "45",
                }
            ),
        ]
        summary = self._run_import(home_rows, online_rows, rows)
        self.assertEqual(summary["skipped"], 2)
        self.assertFalse(
            self.env["irg.gradebook.moodle.course.map"].search(
                [("op_course_id", "=", self.course.id)]
            )
        )

    def test_import_rejects_invalid_ids_and_course_membership(self):
        home_rows = [
            {
                "Odoo Subject Name": self.course.name,
                "Odoo Subject ID": str(self.course.id),
                "Moodle IDs List": "35",
            }
        ]
        invalid_rows = [
            self._assignment_row(**{"Odoo Course ID": value})
            for value in ("1.0", "nan", "inf", "0", "-1", "2147483648")
        ]
        other_course = self.env["op.course"].create(
            {"name": "Curso sin asignatura", "code": "NO-SUBJECT", "lang": "en_US"}
        )
        invalid_rows.append(
            self._assignment_row(**{"Odoo Course ID": str(other_course.id)})
        )
        summary = self._run_import(home_rows, [], invalid_rows)
        self.assertEqual(summary["skipped"], len(invalid_rows))
        self.assertFalse(
            self.env["irg.gradebook.moodle.course.map"].search(
                [("moodle_course_id", "=", 35)]
            )
        )

    def test_views_and_acl_are_loaded(self):
        for xmlid in (
            "irg_gradebook_moodle_routing.irg_gradebook_moodle_course_map_tree",
            "irg_gradebook_moodle_routing.irg_gradebook_moodle_course_map_form",
            "irg_gradebook_moodle_routing.action_irg_gradebook_moodle_course_map",
            "irg_gradebook_moodle_routing.menu_irg_gradebook_moodle_course_map",
            "irg_gradebook_moodle_routing.irg_gradebook_moodle_map_tree_course",
            "irg_gradebook_moodle_routing.irg_gradebook_moodle_map_form_course",
        ):
            self.assertTrue(self.env.ref(xmlid, raise_if_not_found=False), xmlid)

        model = self.env["ir.model"]._get("irg.gradebook.moodle.course.map")
        user_acl = self.env["ir.model.access"].search(
            [
                ("model_id", "=", model.id),
                ("group_id", "=", self.env.ref("base.group_user").id),
            ],
            limit=1,
        )
        system_acl = self.env["ir.model.access"].search(
            [
                ("model_id", "=", model.id),
                ("group_id", "=", self.env.ref("base.group_system").id),
            ],
            limit=1,
        )
        self.assertEqual(
            (user_acl.perm_read, user_acl.perm_write, user_acl.perm_create, user_acl.perm_unlink),
            (True, False, False, False),
        )
        self.assertEqual(
            (system_acl.perm_read, system_acl.perm_write, system_acl.perm_create, system_acl.perm_unlink),
            (True, True, True, True),
        )
