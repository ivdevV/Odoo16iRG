import csv
import io
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from odoo import Command
from odoo.tests import tagged

from ..services.mapping_import import (
    MAX_FILE_SIZE,
    ActivityOperation,
    CourseOperation,
    MappingImportService,
    SubjectOperation,
)
from ..tools import import_mapping
from .common import MappingAdminCommon


COURSE_FIELDS_LEGACY = [
    "Moodle Course ID",
    "Odoo Subject Name",
    "Odoo Subject ID",
    "Nombre del Curso",
]
COURSE_FIELDS_CANONICAL = [
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
class TestMappingImportAnalysis(MappingAdminCommon):
    @staticmethod
    def _csv_payload(fieldnames, rows, encoding="utf-8-sig"):
        stream = io.StringIO(newline="")
        writer = csv.DictWriter(
            stream,
            fieldnames=fieldnames,
            delimiter=";",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)
        return stream.getvalue().encode(encoding)

    def _course_row(self, moodle_course_id=450001, **overrides):
        row = {
            "Moodle Course ID": str(moodle_course_id),
            "Odoo Subject Name": self.course.name,
            "Odoo Subject ID": str(self.course.id),
            "Nombre del Curso": "Curso Test Mapping Admin",
        }
        row.update(overrides)
        return row

    def _canonical_course_row(self, moodle_course_id=450001, **overrides):
        row = {
            "Moodle Course ID": str(moodle_course_id),
            "Odoo Course Name": self.course.name,
            "Odoo Course ID": str(self.course.id),
            "Nombre del Curso": "Curso Test Mapping Admin",
        }
        row.update(overrides)
        return row

    def _assignment_row(self, moodle_course_id=450001, **overrides):
        row = {
            "Curso Nombre": "Curso Test Mapping Admin",
            "Odoo Course ID": str(self.course.id),
            "Moodle Course ID": str(moodle_course_id),
            "Odoo Subject Name": self.subject.name,
            "Odoo Subject ID": str(self.subject.id),
            "Odoo Subject Code": self.subject.code,
            "Moodle IDs List": "501, 502",
            "Moodle Names Found": "Actividad uno|Actividad dos",
        }
        row.update(overrides)
        return row

    def _analyze(
        self,
        course_rows,
        assignment_rows,
        course_fields=COURSE_FIELDS_LEGACY,
        course_encoding="utf-8-sig",
        assignment_encoding="utf-8-sig",
    ):
        return MappingImportService(self.env).analyze_bytes(
            self._csv_payload(course_fields, course_rows, course_encoding),
            self._csv_payload(
                ASSIGNMENT_FIELDS, assignment_rows, assignment_encoding
            ),
        )

    def test_analyzes_utf8_bom_legacy_headers_without_writes(self):
        models = (
            "irg.gradebook.moodle.course.map",
            "irg.gradebook.moodle.map",
            "irg.gradebook.moodle.map.line",
        )
        before = {model: self.env[model].search_count([]) for model in models}

        plan = self._analyze(
            [self._course_row()],
            [self._assignment_row()],
        )

        self.assertEqual(
            plan.courses,
            (
                CourseOperation(
                    self.course.id,
                    self.course.name,
                    450001,
                    "Curso Test Mapping Admin",
                ),
            ),
        )
        self.assertEqual(
            plan.subjects,
            (
                SubjectOperation(
                    self.course.id,
                    self.course.name,
                    450001,
                    self.subject.id,
                    self.subject.name,
                    self.subject.code,
                    "Curso Test Mapping Admin",
                    (
                        ActivityOperation(501, "Actividad uno"),
                        ActivityOperation(502, "Actividad dos"),
                    ),
                ),
            ),
        )
        self.assertEqual(
            plan.summary["courses"],
            {
                "rows_read": 1,
                "rows_accepted": 1,
                "rows_skipped": 0,
                "rows_warned": 0,
                "skipped_by_reason": {},
                "warned_by_reason": {},
            },
        )
        self.assertEqual(plan.summary["assignments"]["rows_accepted"], 1)
        self.assertEqual(
            {model: self.env[model].search_count([]) for model in models},
            before,
        )

    def test_unclosed_quote_after_valid_row_blocks_the_complete_analysis(self):
        valid_courses = self._csv_payload(
            COURSE_FIELDS_LEGACY,
            [self._course_row()],
        )
        malformed_courses = valid_courses + b'"fila sin cerrar'
        assignments = self._csv_payload(ASSIGNMENT_FIELDS, [])
        service = MappingImportService(self.env)

        with patch.object(
            service,
            "_analyze_courses",
            wraps=service._analyze_courses,
        ) as analyze_courses, self.assertRaisesRegex(
            ValueError,
            "CSV courses cannot be parsed",
        ) as raised:
            service.analyze_bytes(malformed_courses, assignments)

        analyze_courses.assert_not_called()
        self.assertNotIn("fila sin cerrar", str(raised.exception))

    def test_preview_counts_mixed_changes_without_writing_inactive_records(self):
        existing_course_map = self.env[
            "irg.gradebook.moodle.course.map"
        ].create(
            {
                "op_course_id": self.course.id,
                "moodle_course_id": 450001,
                "moodle_course_name": "Nombre anterior",
                "active": False,
            }
        )
        existing_subject_map = self.env["irg.gradebook.moodle.map"].create(
            {
                "op_subject_id": self.subject.id,
                "moodle_course_id": 450001,
                "moodle_course_name": "Nombre anterior",
                "course_map_id": existing_course_map.id,
                "active": False,
            }
        )
        lines = self.env["irg.gradebook.moodle.map.line"].create(
            [
                {
                    "map_id": existing_subject_map.id,
                    "moodle_activity_id": 501,
                    "name": "Nombre previo",
                    "activity_type": "assign",
                },
                {
                    "map_id": existing_subject_map.id,
                    "moodle_activity_id": 502,
                    "name": "No vaciar",
                    "activity_type": "assign",
                },
            ]
        )
        before = {
            "course": existing_course_map.read(
                ["moodle_course_name", "active", "write_date"]
            ),
            "subject": existing_subject_map.read(
                ["moodle_course_name", "course_map_id", "active", "write_date"]
            ),
            "lines": lines.read(
                ["moodle_activity_id", "name", "activity_type", "write_date"]
            ),
        }

        plan = self._analyze(
            [
                self._course_row(),
                self._course_row(moodle_course_id=450002),
            ],
            [
                self._assignment_row(
                    **{
                        "Moodle IDs List": "501, 502, 503",
                        "Moodle Names Found": "Nombre nuevo||Actividad nueva",
                    }
                ),
                self._assignment_row(
                    moodle_course_id=450002,
                    **{
                        "Moodle IDs List": "601",
                        "Moodle Names Found": "Actividad del mapa nuevo",
                    }
                ),
            ],
        )

        self.assertEqual(
            plan.summary["course_maps"], {"created": 1, "updated": 1}
        )
        self.assertEqual(
            plan.summary["subject_maps"], {"created": 1, "updated": 1}
        )
        self.assertEqual(
            plan.summary["activities"], {"created": 2, "updated": 1}
        )
        self.env.invalidate_all()
        self.assertEqual(
            {
                "course": existing_course_map.read(
                    ["moodle_course_name", "active", "write_date"]
                ),
                "subject": existing_subject_map.read(
                    [
                        "moodle_course_name",
                        "course_map_id",
                        "active",
                        "write_date",
                    ]
                ),
                "lines": lines.read(
                    [
                        "moodle_activity_id",
                        "name",
                        "activity_type",
                        "write_date",
                    ]
                ),
            },
            before,
        )
        self.assertFalse(existing_course_map.active)
        self.assertFalse(existing_subject_map.active)
        self.assertEqual(lines.mapped("name"), ["Nombre previo", "No vaciar"])

    def test_accepts_macroman_and_canonical_course_headers(self):
        course_name = "Curso Psicología"
        self.course.name = course_name
        plan = self._analyze(
            [
                self._canonical_course_row(
                    **{
                        "Odoo Course Name": "  CURSO   PSICOLOGÍA ",
                        "Nombre del Curso": "Máster Psicología (ONLINE 2026)",
                    }
                ),
                self._canonical_course_row(
                    moodle_course_id=450002,
                    **{
                        "Odoo Course Name": course_name,
                        "Nombre del Curso": "Máster Psicología HomeClass",
                    }
                ),
            ],
            [
                self._assignment_row(
                    **{
                        "Curso Nombre": "  máster psicología (online 2026) ",
                        "Odoo Subject Name": self.subject.name.upper(),
                        "Odoo Subject Code": self.subject.code.lower(),
                    }
                )
            ],
            course_fields=COURSE_FIELDS_CANONICAL,
            course_encoding="mac_roman",
            assignment_encoding="mac_roman",
        )

        self.assertEqual(
            [operation.moodle_course_id for operation in plan.courses],
            [450001, 450002],
        )
        self.assertEqual(len(plan.subjects), 1)
        self.assertEqual(
            plan.courses[0].moodle_course_name,
            "Máster Psicología (ONLINE 2026)",
        )

    def test_rejects_ambiguous_course_aliases_per_row(self):
        fields = COURSE_FIELDS_LEGACY + ["Odoo Course Name", "Odoo Course ID"]
        rows = [
            self._course_row(
                **{
                    "Odoo Course Name": "Otro nombre",
                    "Odoo Course ID": str(self.course.id),
                }
            ),
            self._course_row(
                moodle_course_id=450002,
                **{
                    "Odoo Course Name": self.course.name,
                    "Odoo Course ID": str(self.course.id + 1),
                }
            ),
        ]

        plan = self._analyze(rows, [], course_fields=fields)

        self.assertFalse(plan.courses)
        self.assertEqual(
            plan.summary["courses"]["skipped_by_reason"],
            {"ambiguous_course_alias": 2},
        )

    def test_skips_blank_no_activity_and_invalid_id_rows(self):
        invalid_tokens = ("1.0", "-1", "0", "2147483648", "abc")
        course_rows = [self._course_row()]
        assignment_rows = [
            {field: "" for field in ASSIGNMENT_FIELDS},
            self._assignment_row(**{"Moodle IDs List": ""}),
            *[
                self._assignment_row(
                    **{
                        "Moodle IDs List": token,
                        "Moodle Names Found": "Inválida",
                    }
                )
                for token in invalid_tokens
            ],
        ]

        plan = self._analyze(course_rows, assignment_rows)

        self.assertFalse(plan.subjects)
        self.assertEqual(
            plan.summary["assignments"]["skipped_by_reason"],
            {
                "blank_row": 1,
                "no_activity_ids": 1,
                "invalid_id": len(invalid_tokens),
            },
        )

    def test_skips_invalid_course_ids_and_online_markers(self):
        invalid_ids = ("1.0", "0", "2147483648", "abc")
        rows = [
            *[
                self._course_row(
                    moodle_course_id=450010 + index,
                    **{"Odoo Subject ID": token},
                )
                for index, token in enumerate(invalid_ids)
            ],
            self._course_row(
                moodle_course_id=450020,
                **{"Nombre del Curso": "Curso (ONLINE2026)"},
            ),
            self._course_row(
                moodle_course_id=450021,
                **{"Nombre del Curso": "Curso (ONLINE 26)"},
            ),
        ]

        plan = self._analyze(rows, [])

        self.assertFalse(plan.courses)
        self.assertEqual(
            plan.summary["courses"]["skipped_by_reason"],
            {
                "invalid_id": len(invalid_ids),
                "invalid_online_marker": 2,
            },
        )

    def test_skips_very_long_ascii_id_without_raising(self):
        plan = self._analyze(
            [self._course_row(**{"Odoo Subject ID": "9" * 5000})],
            [],
        )

        self.assertFalse(plan.courses)
        self.assertEqual(
            plan.summary["courses"]["skipped_by_reason"],
            {"invalid_id": 1},
        )

    def test_skips_missing_records_membership_names_code_and_pair(self):
        other_course = self.env["op.course"].create(
            {
                "name": "Curso ajeno",
                "code": "COURSE-OTHER",
                "lang": "en_US",
                "gradebook_id": self.gradebook.id,
            }
        )
        other_subject = self.env["op.subject"].create(
            {
                "name": "Asignatura ajena",
                "code": "SUBJECT-OTHER",
                "course_id": other_course.id,
                "gradebook_id": self.gradebook.id,
            }
        )
        other_course.write({"subject_ids": [Command.link(other_subject.id)]})
        missing_id = 2147483647
        rows = [
            self._assignment_row(moodle_course_id=999001),
            self._assignment_row(**{"Odoo Subject ID": str(missing_id)}),
            self._assignment_row(
                **{
                    "Odoo Subject ID": str(other_subject.id),
                    "Odoo Subject Name": other_subject.name,
                    "Odoo Subject Code": other_subject.code,
                }
            ),
            self._assignment_row(**{"Curso Nombre": "Nombre Moodle incorrecto"}),
            self._assignment_row(**{"Odoo Subject Name": "Nombre incorrecto"}),
            self._assignment_row(**{"Odoo Subject Code": "CODIGO-INCORRECTO"}),
        ]

        plan = self._analyze([self._course_row()], rows)

        self.assertFalse(plan.subjects)
        self.assertEqual(
            plan.summary["assignments"]["skipped_by_reason"],
            {
                "missing_course_pair": 1,
                "missing_odoo_record": 1,
                "subject_not_in_course": 1,
                "name_mismatch": 2,
                "code_mismatch": 1,
            },
        )

    def test_skips_subject_row_with_conflicting_course_parent(self):
        other_course = self.env["op.course"].create(
            {
                "name": "Segundo curso para conflicto de padre",
                "code": "CT-MAP-PARENT-2",
                "lang": "en_US",
                "gradebook_id": self.gradebook.id,
                "subject_ids": [Command.link(self.subject.id)],
            }
        )
        moodle_course_id = 450030
        moodle_course_name = "Curso compartido HomeClass"
        plan = self._analyze(
            [
                self._canonical_course_row(
                    moodle_course_id,
                    **{"Nombre del Curso": moodle_course_name},
                ),
                self._canonical_course_row(
                    moodle_course_id,
                    **{
                        "Odoo Course Name": other_course.name,
                        "Odoo Course ID": str(other_course.id),
                        "Nombre del Curso": moodle_course_name,
                    },
                ),
            ],
            [
                self._assignment_row(
                    moodle_course_id,
                    **{
                        "Curso Nombre": moodle_course_name,
                        "Moodle IDs List": "511",
                        "Moodle Names Found": "Actividad conservada",
                    },
                ),
                self._assignment_row(
                    moodle_course_id,
                    **{
                        "Curso Nombre": moodle_course_name,
                        "Odoo Course ID": str(other_course.id),
                        "Moodle IDs List": "512",
                        "Moodle Names Found": "Actividad conflictiva",
                    },
                ),
            ],
            course_fields=COURSE_FIELDS_CANONICAL,
        )

        self.assertEqual(len(plan.subjects), 1)
        self.assertEqual(plan.subjects[0].op_course_id, self.course.id)
        self.assertEqual(
            plan.subjects[0].activities,
            (ActivityOperation(511, "Actividad conservada"),),
        )
        self.assertEqual(plan.summary["assignments"]["rows_accepted"], 1)
        self.assertEqual(plan.summary["assignments"]["rows_skipped"], 1)
        self.assertEqual(
            plan.summary["assignments"]["skipped_by_reason"],
            {"conflicting_subject_parent": 1},
        )

    def test_deduplicates_and_merges_subject_rows_with_aligned_names(self):
        rows = [
            self._assignment_row(
                **{
                    "Moodle IDs List": "501, 502, 501",
                    "Moodle Names Found": "|Actividad dos|Actividad uno",
                }
            ),
            self._assignment_row(
                **{
                    "Moodle IDs List": "502,503",
                    "Moodle Names Found": "Nombre ignorado",
                }
            ),
        ]

        plan = self._analyze([self._course_row()], rows)

        self.assertEqual(
            plan.subjects[0].activities,
            (
                ActivityOperation(501, "Actividad uno"),
                ActivityOperation(502, "Actividad dos"),
                ActivityOperation(503, ""),
            ),
        )
        self.assertEqual(plan.summary["assignments"]["rows_accepted"], 2)
        self.assertEqual(plan.summary["assignments"]["rows_warned"], 2)
        self.assertEqual(
            plan.summary["assignments"]["warned_by_reason"],
            {
                "duplicate_activity_id": 1,
                "activity_name_count_mismatch": 1,
            },
        )

    def test_rejects_oversized_payload_and_missing_headers_safely(self):
        with self.assertRaisesRegex(ValueError, "10 MiB"):
            MappingImportService(self.env).analyze_bytes(
                b"x" * (MAX_FILE_SIZE + 1),
                self._csv_payload(ASSIGNMENT_FIELDS, []),
            )
        with self.assertRaisesRegex(ValueError, "courses.*header") as caught:
            MappingImportService(self.env).analyze_bytes(
                self._csv_payload(["Moodle Course ID"], []),
                self._csv_payload(ASSIGNMENT_FIELDS, []),
            )
        self.assertNotIn("Moodle Course ID", str(caught.exception))

    def test_shell_adapter_matches_binary_analysis(self):
        courses_payload = self._csv_payload(
            COURSE_FIELDS_LEGACY, [self._course_row()]
        )
        assignments_payload = self._csv_payload(
            ASSIGNMENT_FIELDS, [self._assignment_row()]
        )
        expected = MappingImportService(self.env).analyze_bytes(
            courses_payload, assignments_payload
        )

        with TemporaryDirectory() as directory:
            courses_path = Path(directory) / "mapeo cursos.csv"
            assignments_path = Path(directory) / "Mapeo asignaturas.csv"
            courses_path.write_bytes(courses_payload)
            assignments_path.write_bytes(assignments_payload)

            actual = import_mapping.analyze_paths(
                self.env, str(courses_path), str(assignments_path)
            )

        self.assertEqual(actual, expected)

    def test_shell_adapter_rejects_relative_and_oversized_paths(self):
        with self.assertRaisesRegex(ValueError, "absoluta"):
            import_mapping.analyze_paths(
                self.env, "mapeo cursos.csv", "Mapeo asignaturas.csv"
            )

        with TemporaryDirectory() as directory:
            oversized_path = Path(directory) / "oversized.csv"
            assignments_path = Path(directory) / "Mapeo asignaturas.csv"
            oversized_path.write_bytes(b"x" * (MAX_FILE_SIZE + 1))
            assignments_path.write_bytes(
                self._csv_payload(ASSIGNMENT_FIELDS, [])
            )
            with patch.object(
                MappingImportService, "analyze_bytes"
            ) as analyze_bytes:
                with self.assertRaisesRegex(ValueError, "10 MiB"):
                    import_mapping.analyze_paths(
                        self.env,
                        str(oversized_path),
                        str(assignments_path),
                    )
                analyze_bytes.assert_not_called()
