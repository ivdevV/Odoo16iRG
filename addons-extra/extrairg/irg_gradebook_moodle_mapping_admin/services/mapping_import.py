import csv
import io
from dataclasses import dataclass

from odoo.exceptions import ValidationError

from odoo.addons.irg_gradebook_moodle_routing.models.moodle_routing import (
    parse_moodle_course_name,
)


CSV_DELIMITER = ";"
MAX_FILE_SIZE = 10 * 1024 * 1024
MIN_ID = 1
MAX_ID = 2147483647

COURSE_MOODLE_ID_HEADER = "Moodle Course ID"
COURSE_MOODLE_NAME_HEADER = "Nombre del Curso"
COURSE_NAME_HEADERS = ("Odoo Subject Name", "Odoo Course Name")
COURSE_ID_HEADERS = ("Odoo Subject ID", "Odoo Course ID")
ASSIGNMENT_HEADERS = {
    "Curso Nombre",
    "Odoo Course ID",
    "Moodle Course ID",
    "Odoo Subject Name",
    "Odoo Subject ID",
    "Odoo Subject Code",
    "Moodle IDs List",
    "Moodle Names Found",
}


@dataclass(frozen=True)
class CourseOperation:
    op_course_id: int
    op_course_name: str
    moodle_course_id: int
    moodle_course_name: str


@dataclass(frozen=True)
class ActivityOperation:
    moodle_activity_id: int
    name: str


@dataclass(frozen=True)
class SubjectOperation:
    op_course_id: int
    op_course_name: str
    moodle_course_id: int
    op_subject_id: int
    op_subject_name: str
    op_subject_code: str
    moodle_course_name: str
    activities: tuple


@dataclass(frozen=True)
class ImportPlan:
    courses: tuple
    subjects: tuple
    summary: dict


@dataclass(frozen=True)
class _CsvRows:
    headers: tuple
    rows: tuple


def _normalize_text(value):
    return " ".join(str(value or "").split()).casefold()


def _parse_id(value):
    token = str(value or "").strip()
    if not token.isascii() or not token.isdigit():
        return None
    significant_token = token.lstrip("0") or "0"
    maximum_token = str(MAX_ID)
    if len(significant_token) > len(maximum_token) or (
        len(significant_token) == len(maximum_token)
        and significant_token > maximum_token
    ):
        return None
    identifier = int(significant_token)
    if not MIN_ID <= identifier <= MAX_ID:
        return None
    return identifier


def _empty_stats():
    return {
        "rows_read": 0,
        "rows_accepted": 0,
        "rows_skipped": 0,
        "rows_warned": 0,
        "skipped_by_reason": {},
        "warned_by_reason": {},
    }


def _count_reason(stats, bucket, reason):
    reasons = stats[bucket]
    reasons[reason] = reasons.get(reason, 0) + 1


def _skip(stats, reason):
    stats["rows_skipped"] += 1
    _count_reason(stats, "skipped_by_reason", reason)


def _warn(stats, reasons):
    if not reasons:
        return
    stats["rows_warned"] += 1
    for reason in reasons:
        _count_reason(stats, "warned_by_reason", reason)


def _row_is_blank(row):
    return not any(
        str(value or "").strip()
        for header, value in row.items()
        if header is not None
    )


def _resolve_alias(row, legacy_header, canonical_header):
    legacy = str(row.get(legacy_header) or "").strip()
    canonical = str(row.get(canonical_header) or "").strip()
    if legacy and canonical and _normalize_text(legacy) != _normalize_text(canonical):
        return "", True
    return canonical or legacy, False


class MappingImportService:
    def __init__(self, env):
        self.env = env

    def analyze_bytes(self, courses_payload, assignments_payload):
        course_rows = self._read_csv(courses_payload, "courses")
        assignment_rows = self._read_csv(assignments_payload, "assignments")
        courses, course_stats = self._analyze_courses(course_rows)
        subjects, subject_stats = self._analyze_subjects(
            assignment_rows, courses
        )
        preview = self._preview_changes(
            tuple(courses.values()), tuple(subjects.values())
        )
        return ImportPlan(
            tuple(courses.values()),
            tuple(subjects.values()),
            self._build_summary(course_stats, subject_stats, preview),
        )

    def apply_plan(self, plan):
        self._preflight_plan(plan)
        result = self._empty_apply_result()
        course_maps = {}
        for operation in plan.courses:
            self._revalidate_course(operation)
            record = self._upsert_course(operation, result)
            course_maps[
                (operation.op_course_id, operation.moodle_course_id)
            ] = record
        for operation in plan.subjects:
            parent = course_maps.get(
                (operation.op_course_id, operation.moodle_course_id)
            )
            if not parent:
                raise ValidationError(
                    "La asignatura no tiene un mapa de curso válido en el plan."
                )
            self._revalidate_subject(operation, parent)
            mapping = self._upsert_subject(operation, parent, result)
            self._upsert_activities(operation.activities, mapping, result)
        result["affected_course_map_ids"] = sorted(
            set(result["affected_course_map_ids"])
        )
        result["affected_subject_map_ids"] = sorted(
            set(result["affected_subject_map_ids"])
        )
        return result

    def _preflight_plan(self, plan):
        if (
            not isinstance(plan, ImportPlan)
            or not isinstance(plan.courses, tuple)
            or not isinstance(plan.subjects, tuple)
            or not isinstance(plan.summary, dict)
        ):
            raise ValidationError("El plan de importación no es válido.")

        courses_by_key = {}
        for operation in plan.courses:
            self._preflight_course_operation(operation)
            key = (operation.op_course_id, operation.moodle_course_id)
            if key in courses_by_key:
                raise ValidationError("El plan contiene cursos duplicados.")
            courses_by_key[key] = operation

        subject_keys = set()
        for operation in plan.subjects:
            self._preflight_subject_operation(operation, courses_by_key)
            subject_key = (
                operation.op_subject_id,
                operation.moodle_course_id,
            )
            if subject_key in subject_keys:
                raise ValidationError("El plan contiene asignaturas duplicadas.")
            subject_keys.add(subject_key)

    def _preflight_course_operation(self, operation):
        if not isinstance(operation, CourseOperation):
            raise ValidationError("La operación de curso no es válida.")
        if (
            not self._valid_operation_id(operation.op_course_id)
            or not self._valid_operation_id(operation.moodle_course_id)
            or not isinstance(operation.op_course_name, str)
            or not isinstance(operation.moodle_course_name, str)
            or not operation.op_course_name.strip()
            or not operation.moodle_course_name.strip()
        ):
            raise ValidationError("La operación de curso no es válida.")
        modality, _edition_year = parse_moodle_course_name(
            operation.moodle_course_name.strip()
        )
        if not modality:
            raise ValidationError("El nombre del curso Moodle no es válido.")

    def _preflight_subject_operation(self, operation, courses_by_key):
        if not isinstance(operation, SubjectOperation):
            raise ValidationError("La operación de asignatura no es válida.")
        if (
            not self._valid_operation_id(operation.op_course_id)
            or not self._valid_operation_id(operation.moodle_course_id)
            or not self._valid_operation_id(operation.op_subject_id)
            or not isinstance(operation.op_course_name, str)
            or not isinstance(operation.op_subject_name, str)
            or not isinstance(operation.op_subject_code, str)
            or not isinstance(operation.moodle_course_name, str)
            or not isinstance(operation.activities, tuple)
            or not operation.op_course_name.strip()
            or not operation.op_subject_name.strip()
            or not operation.moodle_course_name.strip()
            or not operation.activities
        ):
            raise ValidationError("La operación de asignatura no es válida.")

        parent = courses_by_key.get(
            (operation.op_course_id, operation.moodle_course_id)
        )
        if (
            not parent
            or _normalize_text(parent.op_course_name)
            != _normalize_text(operation.op_course_name)
            or _normalize_text(parent.moodle_course_name)
            != _normalize_text(operation.moodle_course_name)
        ):
            raise ValidationError(
                "La asignatura no tiene un curso coherente en el plan."
            )

        activity_ids = set()
        for activity in operation.activities:
            if not isinstance(activity, ActivityOperation):
                raise ValidationError("La operación de actividad no es válida.")
            if (
                not self._valid_operation_id(activity.moodle_activity_id)
                or not isinstance(activity.name, str)
            ):
                raise ValidationError("La operación de actividad no es válida.")
            if activity.moodle_activity_id in activity_ids:
                raise ValidationError("El plan contiene actividades duplicadas.")
            activity_ids.add(activity.moodle_activity_id)

    @staticmethod
    def _empty_apply_result():
        return {
            "course_maps": {"created": 0, "updated": 0},
            "subject_maps": {"created": 0, "updated": 0},
            "activities": {"created": 0, "updated": 0},
            "affected_course_map_ids": [],
            "affected_subject_map_ids": [],
        }

    @staticmethod
    def _valid_operation_id(identifier):
        return (
            isinstance(identifier, int)
            and not isinstance(identifier, bool)
            and MIN_ID <= identifier <= MAX_ID
        )

    def _revalidate_course(self, operation):
        if not isinstance(operation, CourseOperation) or not all(
            (
                self._valid_operation_id(operation.op_course_id),
                self._valid_operation_id(operation.moodle_course_id),
                isinstance(operation.op_course_name, str),
                operation.op_course_name.strip(),
                isinstance(operation.moodle_course_name, str),
                operation.moodle_course_name.strip(),
            )
        ):
            raise ValidationError("La operación de curso no es válida.")
        modality, _edition_year = parse_moodle_course_name(
            operation.moodle_course_name.strip()
        )
        if not modality:
            raise ValidationError("El nombre del curso Moodle no es válido.")
        course = self.env["op.course"].browse(operation.op_course_id).exists()
        if not course:
            raise ValidationError("El curso Odoo ya no existe.")
        if _normalize_text(course.name) != _normalize_text(
            operation.op_course_name
        ):
            raise ValidationError("El curso Odoo ya no existe o no es válido.")
        return course

    def _upsert_course(self, operation, result):
        course_map_model = self.env[
            "irg.gradebook.moodle.course.map"
        ].with_context(active_test=False)
        course_map = self._find_course_map(operation)
        values = {
            "moodle_course_name": operation.moodle_course_name.strip(),
            "active": True,
        }
        if course_map:
            course_map.write(values)
            result["course_maps"]["updated"] += 1
        else:
            course_map = course_map_model.create(
                dict(
                    values,
                    op_course_id=operation.op_course_id,
                    moodle_course_id=operation.moodle_course_id,
                )
            )
            result["course_maps"]["created"] += 1
        result["affected_course_map_ids"].append(course_map.id)
        return course_map

    def _revalidate_subject(self, operation, parent):
        if not isinstance(operation, SubjectOperation) or not all(
            (
                self._valid_operation_id(operation.op_course_id),
                self._valid_operation_id(operation.moodle_course_id),
                self._valid_operation_id(operation.op_subject_id),
                isinstance(operation.op_course_name, str),
                operation.op_course_name.strip(),
                isinstance(operation.op_subject_name, str),
                operation.op_subject_name.strip(),
                isinstance(operation.op_subject_code, str),
                isinstance(operation.moodle_course_name, str),
                operation.moodle_course_name.strip(),
                isinstance(operation.activities, tuple),
            )
        ):
            raise ValidationError("La operación de asignatura no es válida.")
        parent = parent.exists()
        if (
            not parent
            or parent.op_course_id.id != operation.op_course_id
            or parent.moodle_course_id != operation.moodle_course_id
            or _normalize_text(parent.moodle_course_name)
            != _normalize_text(operation.moodle_course_name)
        ):
            raise ValidationError(
                "El mapa de curso padre no coincide con la asignatura."
            )
        course = self.env["op.course"].browse(operation.op_course_id).exists()
        subject = self.env["op.subject"].browse(operation.op_subject_id).exists()
        if not course or not subject:
            raise ValidationError("El curso o la asignatura Odoo ya no existe.")
        if _normalize_text(course.name) != _normalize_text(
            operation.op_course_name
        ):
            raise ValidationError("El nombre del curso Odoo ha cambiado.")
        if _normalize_text(subject.name) != _normalize_text(
            operation.op_subject_name
        ):
            raise ValidationError("El nombre de la asignatura Odoo ha cambiado.")
        if _normalize_text(subject.code) != _normalize_text(
            operation.op_subject_code
        ):
            raise ValidationError("El código de la asignatura Odoo ha cambiado.")
        if subject not in course.subject_ids:
            raise ValidationError(
                "La asignatura ya no pertenece al curso Odoo."
            )
        for activity in operation.activities:
            if (
                not isinstance(activity, ActivityOperation)
                or not self._valid_operation_id(activity.moodle_activity_id)
                or not isinstance(activity.name, str)
            ):
                raise ValidationError("La operación de actividad no es válida.")
        return subject

    def _upsert_subject(self, operation, parent, result):
        subject_map_model = self.env["irg.gradebook.moodle.map"].with_context(
            active_test=False
        )
        subject_map = self._find_subject_map(operation)
        values = {
            "course_map_id": parent.id,
            "moodle_course_name": operation.moodle_course_name.strip(),
            "active": True,
        }
        if subject_map:
            subject_map.write(values)
            result["subject_maps"]["updated"] += 1
        else:
            subject_map = subject_map_model.create(
                dict(
                    values,
                    op_subject_id=operation.op_subject_id,
                    moodle_course_id=operation.moodle_course_id,
                )
            )
            result["subject_maps"]["created"] += 1
        result["affected_subject_map_ids"].append(subject_map.id)
        return subject_map

    def _upsert_activities(self, operations, mapping, result):
        line_model = self.env[
            "irg.gradebook.moodle.map.line"
        ].with_context(active_test=False)
        for operation in operations:
            line = self._find_activity(mapping, operation)
            name = operation.name.strip()
            if line:
                if name:
                    line.write({"name": name})
                    result["activities"]["updated"] += 1
                continue
            line_model.create(
                {
                    "map_id": mapping.id,
                    "moodle_activity_id": operation.moodle_activity_id,
                    "name": name or False,
                    "activity_type": "quiz",
                }
            )
            result["activities"]["created"] += 1

    def _preview_changes(self, courses, subjects):
        preview = {
            "course_maps": {"created": 0, "updated": 0},
            "subject_maps": {"created": 0, "updated": 0},
            "activities": {"created": 0, "updated": 0},
        }
        for operation in courses:
            existing = self._find_course_map(operation)
            bucket = "updated" if existing else "created"
            preview["course_maps"][bucket] += 1

        for operation in subjects:
            mapping = self._find_subject_map(operation)
            bucket = "updated" if mapping else "created"
            preview["subject_maps"][bucket] += 1
            for activity in operation.activities:
                line = mapping and self._find_activity(mapping, activity)
                if not line:
                    preview["activities"]["created"] += 1
                elif activity.name.strip():
                    preview["activities"]["updated"] += 1
        return preview

    def _find_course_map(self, operation):
        return self.env["irg.gradebook.moodle.course.map"].with_context(
            active_test=False
        ).search(
            [
                ("op_course_id", "=", operation.op_course_id),
                ("moodle_course_id", "=", operation.moodle_course_id),
            ],
            limit=1,
        )

    def _find_subject_map(self, operation):
        return self.env["irg.gradebook.moodle.map"].with_context(
            active_test=False
        ).search(
            [
                ("op_subject_id", "=", operation.op_subject_id),
                ("moodle_course_id", "=", operation.moodle_course_id),
            ],
            limit=1,
        )

    def _find_activity(self, mapping, operation):
        return self.env["irg.gradebook.moodle.map.line"].with_context(
            active_test=False
        ).search(
            [
                ("map_id", "=", mapping.id),
                ("moodle_activity_id", "=", operation.moodle_activity_id),
            ],
            limit=1,
        )

    @staticmethod
    def _read_csv(payload, source_name):
        if not isinstance(payload, (bytes, bytearray)):
            raise ValueError("CSV %s: invalid binary payload" % source_name)
        if len(payload) > MAX_FILE_SIZE:
            raise ValueError("CSV %s exceeds 10 MiB" % source_name)
        try:
            text = bytes(payload).decode("utf-8-sig")
        except UnicodeDecodeError:
            text = bytes(payload).decode("mac_roman")
        try:
            reader = csv.DictReader(
                io.StringIO(text), delimiter=CSV_DELIMITER, strict=True
            )
            headers = tuple(reader.fieldnames or ())
            rows = tuple((reader.line_num, row) for row in reader)
        except csv.Error as error:
            raise ValueError("CSV %s cannot be parsed" % source_name) from error
        return _CsvRows(headers, rows)

    def _analyze_courses(self, source):
        self._validate_course_headers(source.headers)
        stats = _empty_stats()
        courses = {}
        course_model = self.env["op.course"]
        for _line_number, row in source.rows:
            stats["rows_read"] += 1
            if _row_is_blank(row):
                _skip(stats, "blank_row")
                continue

            course_name, ambiguous_name = _resolve_alias(
                row, *COURSE_NAME_HEADERS
            )
            course_id_token, ambiguous_id = _resolve_alias(
                row, *COURSE_ID_HEADERS
            )
            if ambiguous_name or ambiguous_id:
                _skip(stats, "ambiguous_course_alias")
                continue

            op_course_id = _parse_id(course_id_token)
            moodle_course_id = _parse_id(row.get(COURSE_MOODLE_ID_HEADER))
            if not op_course_id or not moodle_course_id:
                _skip(stats, "invalid_id")
                continue

            moodle_course_name = str(
                row.get(COURSE_MOODLE_NAME_HEADER) or ""
            ).strip()
            modality, _edition_year = parse_moodle_course_name(
                moodle_course_name
            )
            if not modality:
                _skip(stats, "invalid_online_marker")
                continue

            course = course_model.browse(op_course_id).exists()
            if not course:
                _skip(stats, "missing_odoo_record")
                continue
            if _normalize_text(course_name) != _normalize_text(course.name):
                _skip(stats, "name_mismatch")
                continue

            key = (op_course_id, moodle_course_id)
            previous = courses.get(key)
            if previous and _normalize_text(
                previous.moodle_course_name
            ) != _normalize_text(moodle_course_name):
                _skip(stats, "name_mismatch")
                continue
            courses.setdefault(
                key,
                CourseOperation(
                    op_course_id,
                    course_name,
                    moodle_course_id,
                    moodle_course_name,
                ),
            )
            stats["rows_accepted"] += 1
        return courses, stats

    def _analyze_subjects(self, source, courses):
        self._validate_assignment_headers(source.headers)
        stats = _empty_stats()
        subjects = {}
        course_model = self.env["op.course"]
        subject_model = self.env["op.subject"]
        for _line_number, row in source.rows:
            stats["rows_read"] += 1
            if _row_is_blank(row):
                _skip(stats, "blank_row")
                continue

            op_course_id = _parse_id(row.get("Odoo Course ID"))
            moodle_course_id = _parse_id(row.get("Moodle Course ID"))
            op_subject_id = _parse_id(row.get("Odoo Subject ID"))
            activity_ids, activity_id_error = self._parse_activity_ids(
                row.get("Moodle IDs List")
            )
            if activity_id_error == "no_activity_ids":
                _skip(stats, activity_id_error)
                continue
            if (
                not op_course_id
                or not moodle_course_id
                or not op_subject_id
                or activity_id_error
            ):
                _skip(stats, "invalid_id")
                continue

            course_operation = courses.get((op_course_id, moodle_course_id))
            if not course_operation:
                _skip(stats, "missing_course_pair")
                continue

            course = course_model.browse(op_course_id).exists()
            subject = subject_model.browse(op_subject_id).exists()
            if not course or not subject:
                _skip(stats, "missing_odoo_record")
                continue
            if subject not in course.subject_ids:
                _skip(stats, "subject_not_in_course")
                continue
            if (
                _normalize_text(row.get("Curso Nombre"))
                != _normalize_text(course_operation.moodle_course_name)
                or _normalize_text(row.get("Odoo Subject Name"))
                != _normalize_text(subject.name)
            ):
                _skip(stats, "name_mismatch")
                continue
            if _normalize_text(row.get("Odoo Subject Code")) != _normalize_text(
                subject.code
            ):
                _skip(stats, "code_mismatch")
                continue

            key = (op_subject_id, moodle_course_id)
            previous = subjects.get(key)
            if previous and previous.op_course_id != op_course_id:
                _skip(stats, "conflicting_subject_parent")
                continue

            activities, warnings = self._align_activities(
                activity_ids, row.get("Moodle Names Found")
            )
            if previous:
                activities = self._merge_activities(
                    previous.activities, activities
                )
            subjects[key] = SubjectOperation(
                op_course_id,
                previous.op_course_name
                if previous
                else course_operation.op_course_name,
                moodle_course_id,
                op_subject_id,
                previous.op_subject_name
                if previous
                else str(row.get("Odoo Subject Name") or "").strip(),
                previous.op_subject_code
                if previous
                else str(row.get("Odoo Subject Code") or "").strip(),
                course_operation.moodle_course_name,
                tuple(activities),
            )
            stats["rows_accepted"] += 1
            _warn(stats, warnings)
        return subjects, stats

    @staticmethod
    def _validate_course_headers(headers):
        header_set = set(headers)
        valid = (
            COURSE_MOODLE_ID_HEADER in header_set
            and COURSE_MOODLE_NAME_HEADER in header_set
            and any(header in header_set for header in COURSE_NAME_HEADERS)
            and any(header in header_set for header in COURSE_ID_HEADERS)
        )
        if not valid:
            raise ValueError("CSV courses: missing required header(s)")

    @staticmethod
    def _validate_assignment_headers(headers):
        if not ASSIGNMENT_HEADERS.issubset(set(headers)):
            raise ValueError("CSV assignments: missing required header(s)")

    @staticmethod
    def _parse_activity_ids(value):
        token = str(value or "").strip()
        if not token:
            return (), "no_activity_ids"
        parts = [part.strip() for part in token.split(",")]
        parsed = tuple(_parse_id(part) for part in parts)
        if any(identifier is None for identifier in parsed):
            return (), "invalid_id"
        return parsed, None

    @staticmethod
    def _align_activities(activity_ids, names_value):
        names_token = str(names_value or "")
        names = (
            [name.strip() for name in names_token.split("|")]
            if names_token
            else []
        )
        warnings = []
        if len(names) != len(activity_ids):
            warnings.append("activity_name_count_mismatch")
        if len(set(activity_ids)) != len(activity_ids):
            warnings.append("duplicate_activity_id")

        aligned = {}
        for index, activity_id in enumerate(activity_ids):
            name = names[index] if index < len(names) else ""
            if activity_id not in aligned or (not aligned[activity_id] and name):
                aligned[activity_id] = name
        return tuple(
            ActivityOperation(activity_id, name)
            for activity_id, name in aligned.items()
        ), warnings

    @staticmethod
    def _merge_activities(existing, incoming):
        merged = {activity.moodle_activity_id: activity.name for activity in existing}
        for activity in incoming:
            current_name = merged.get(activity.moodle_activity_id)
            if activity.moodle_activity_id not in merged or (
                not current_name and activity.name
            ):
                merged[activity.moodle_activity_id] = activity.name
        return tuple(
            ActivityOperation(activity_id, name)
            for activity_id, name in merged.items()
        )

    @staticmethod
    def _build_summary(course_stats, subject_stats, preview):
        summary = {
            "courses": course_stats,
            "assignments": subject_stats,
        }
        summary.update(preview)
        return summary
