import csv
from contextlib import redirect_stdout
import importlib.util
from io import StringIO
from pathlib import Path
import tempfile

from odoo.tests import TransactionCase, tagged


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "tools" / "import_map_csv.py"
)
CSV_FIELDS = (
    "Moodle Course ID",
    "Odoo Subject ID",
    "Odoo Subject Name",
    "Curso Nombre",
    "Moodle IDs List",
    "Moodle Names Found",
)


def _load_import_module():
    spec = importlib.util.spec_from_file_location(
        "irg_gradebook_moodle_map_csv_import", SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@tagged("post_install", "-at_install")
class TestImportMapCsv(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.gradebook = cls.env["app.gradebook"].create(
            {
                "name": "Import map CSV",
                "grading_scale": 10,
                "gradebook_template_ids": [
                    (0, 0, {"type": "exam", "weight": 100, "qty": 1})
                ],
            }
        )
        cls.course = cls.env["op.course"].create(
            {
                "name": "Import map CSV",
                "code": "IMCSV",
                "lang": "en_US",
                "gradebook_id": cls.gradebook.id,
            }
        )
        cls.subject = cls.env["op.subject"].create(
            {
                "name": "Subject import map CSV",
                "code": "IMCSV-SUBJECT",
                "course_id": cls.course.id,
                "gradebook_id": cls.gradebook.id,
            }
        )

    def _write_csv(self, csv_path, activity_ids, activity_names, course_name):
        rows = [
            {
                "Moodle Course ID": "808008",
                "Odoo Subject ID": str(self.subject.id),
                "Odoo Subject Name": self.subject.name,
                "Curso Nombre": course_name,
                "Moodle IDs List": ", ".join(map(str, activity_ids)),
                "Moodle Names Found": " | ".join(activity_names),
            },
            {
                "Moodle Course ID": "909009",
                "Odoo Subject ID": "2147483647",
                "Odoo Subject Name": "Subject absent from local database",
                "Curso Nombre": "Missing subject course",
                "Moodle IDs List": "999001",
                "Moodle Names Found": "Missing subject quiz",
            },
        ]
        with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def _run_import_rows(self, import_module, rows):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "map_asignaturas.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            output = StringIO()
            with redirect_stdout(output):
                import_module.run_import(self.env, str(csv_path))
        return output.getvalue()

    def test_import_creates_then_updates_map_and_regenerates_quiz_lines(self):
        self.assertTrue(
            SCRIPT_PATH.is_file(),
            "TDD RED: falta tools/import_map_csv.py",
        )
        import_module = _load_import_module()
        map_model = self.env["irg.gradebook.moodle.map"]
        domain = [
            ("op_subject_id", "=", self.subject.id),
            ("moodle_course_id", "=", 808008),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "map_asignaturas.csv"
            self._write_csv(
                csv_path,
                (700001, 700002),
                ("Quiz inicial 1", "Quiz inicial 2"),
                "Curso inicial",
            )
            first_output = StringIO()
            with redirect_stdout(first_output):
                import_module.run_import(self.env, str(csv_path))

            mapping = map_model.search(domain)
            self.assertEqual(len(mapping), 1)
            self.assertEqual(mapping.moodle_course_name, "Curso inicial")
            self.assertEqual(
                mapping.line_ids.mapped("moodle_activity_id"),
                [700001, 700002],
            )
            self.assertEqual(
                mapping.line_ids.mapped("name"),
                ["Quiz inicial 1", "Quiz inicial 2"],
            )
            self.assertEqual(set(mapping.line_ids.mapped("activity_type")), {"quiz"})
            self.assertIn(
                "SKIP: op.subject 2147483647 no existe",
                first_output.getvalue(),
            )
            self.assertIn(
                "Import mapeo: 1 creados, 0 actualizados, 1 saltados.",
                first_output.getvalue(),
            )

            self._write_csv(
                csv_path,
                (700003, 700004, 700005),
                ("Quiz nuevo 1", "Quiz nuevo 2", "Quiz nuevo 3"),
                "Curso actualizado",
            )
            second_output = StringIO()
            with redirect_stdout(second_output):
                import_module.run_import(self.env, str(csv_path))

        self.assertEqual(map_model.search_count(domain), 1)
        mapping = map_model.search(domain)
        self.assertEqual(mapping.moodle_course_name, "Curso actualizado")
        self.assertEqual(
            mapping.line_ids.mapped("moodle_activity_id"),
            [700003, 700004, 700005],
        )
        self.assertEqual(
            mapping.line_ids.mapped("name"),
            ["Quiz nuevo 1", "Quiz nuevo 2", "Quiz nuevo 3"],
        )
        self.assertEqual(set(mapping.line_ids.mapped("activity_type")), {"quiz"})
        self.assertIn(
            "Import mapeo: 0 creados, 1 actualizados, 1 saltados.",
            second_output.getvalue(),
        )

    def test_invalid_activity_lists_preserve_existing_map_and_lines(self):
        import_module = _load_import_module()
        mapping = self.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": self.subject.id,
                "moodle_course_id": 808108,
                "moodle_course_name": "Curso preservado",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "moodle_activity_id": 710001,
                            "name": "Quiz preservado 1",
                            "activity_type": "quiz",
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "moodle_activity_id": 710002,
                            "name": "Quiz preservado 2",
                            "activity_type": "quiz",
                        },
                    ),
                ],
            }
        )
        original_lines = [
            (
                line.id,
                line.moodle_activity_id,
                line.name,
                line.activity_type,
            )
            for line in mapping.line_ids
        ]

        for invalid_ids in ("", "abc", "123,abc"):
            with self.subTest(invalid_ids=invalid_ids):
                output = self._run_import_rows(
                    import_module,
                    [
                        {
                            "Moodle Course ID": "808108",
                            "Odoo Subject ID": str(self.subject.id),
                            "Odoo Subject Name": self.subject.name,
                            "Curso Nombre": "Curso que no debe actualizarse",
                            "Moodle IDs List": invalid_ids,
                            "Moodle Names Found": "Nombre que no debe persistir",
                        }
                    ],
                )
                self.assertEqual(mapping.moodle_course_name, "Curso preservado")
                self.assertEqual(
                    [
                        (
                            line.id,
                            line.moodle_activity_id,
                            line.name,
                            line.activity_type,
                        )
                        for line in mapping.line_ids
                    ],
                    original_lines,
                )
                self.assertIn(
                    "Import mapeo: 0 creados, 0 actualizados, 1 saltados.",
                    output,
                )

    def test_invalid_subject_or_course_ids_are_skipped_before_valid_row(self):
        import_module = _load_import_module()
        rows = []
        for field_name, invalid_value in (
            ("Odoo Subject ID", "inf"),
            ("Odoo Subject ID", "1e309"),
            ("Odoo Subject ID", "malformed"),
            ("Moodle Course ID", "inf"),
            ("Moodle Course ID", "1e309"),
            ("Moodle Course ID", "malformed"),
        ):
            row = {
                "Moodle Course ID": "808208",
                "Odoo Subject ID": str(self.subject.id),
                "Odoo Subject Name": self.subject.name,
                "Curso Nombre": "Curso inválido",
                "Moodle IDs List": "720001",
                "Moodle Names Found": "Quiz inválido",
            }
            row[field_name] = invalid_value
            rows.append(row)
        rows.append(
            {
                "Moodle Course ID": "808209",
                "Odoo Subject ID": str(self.subject.id),
                "Odoo Subject Name": self.subject.name,
                "Curso Nombre": "Curso válido final",
                "Moodle IDs List": "720009",
                "Moodle Names Found": "Quiz válido final",
            }
        )

        try:
            output = self._run_import_rows(import_module, rows)
        except Exception as error:  # pylint: disable=broad-except
            self.fail(
                "El import debe saltar IDs inválidos y continuar: %s: %s"
                % (type(error).__name__, error)
            )

        mapping = self.env["irg.gradebook.moodle.map"].search(
            [
                ("op_subject_id", "=", self.subject.id),
                ("moodle_course_id", "=", 808209),
            ]
        )
        self.assertEqual(len(mapping), 1)
        self.assertEqual(mapping.moodle_course_name, "Curso válido final")
        self.assertEqual(mapping.line_ids.moodle_activity_id, 720009)
        self.assertEqual(mapping.line_ids.name, "Quiz válido final")
        self.assertIn(
            "Import mapeo: 1 creados, 0 actualizados, 6 saltados.",
            output,
        )
