import csv
import re

from odoo.addons.irg_gradebook_moodle_routing.models.moodle_routing import (
    parse_moodle_course_name,
)


ODOO_INTEGER_ID_MIN = 1
ODOO_INTEGER_ID_MAX = 2147483647
POSITIVE_INTEGER_RE = re.compile(r"[0-9]+")
HOMECLASS_REQUIRED_HEADERS = {"Odoo Subject ID", "Moodle IDs List"}
ONLINE_REQUIRED_HEADERS = {"ID Curso"}
ASSIGNMENTS_REQUIRED_HEADERS = {
    "Curso Nombre",
    "Odoo Course ID",
    "Moodle Course ID",
    "Odoo Subject Name",
    "Odoo Subject ID",
    "Moodle IDs List",
    "Moodle Names Found",
}


def _parse_id(value):
    token = str(value or "").strip()
    if not POSITIVE_INTEGER_RE.fullmatch(token):
        return None
    parsed = int(token)
    if not ODOO_INTEGER_ID_MIN <= parsed <= ODOO_INTEGER_ID_MAX:
        return None
    return parsed


def _parse_id_list(value):
    tokens = [token.strip() for token in str(value or "").split(",")]
    if not tokens or not all(tokens):
        return None
    parsed = [_parse_id(token) for token in tokens]
    if any(identifier is None for identifier in parsed):
        return None
    if len(set(parsed)) != len(parsed):
        return None
    return parsed


def _read_rows(path, source_name, required_headers):
    with open(path, newline="", encoding="mac_roman") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        headers = set(reader.fieldnames or [])
        missing_headers = sorted(required_headers - headers)
        if missing_headers:
            raise ValueError(
                "CSV %s: faltan encabezados obligatorios: %s"
                % (source_name, ", ".join(missing_headers))
            )
        yield from reader


def _source_stats():
    return {
        "rows_read": 0,
        "rows_accepted": 0,
        "rows_discarded": 0,
        "discarded_by_reason": {},
    }


def _discard_source(stats, reason):
    stats["rows_discarded"] += 1
    reasons = stats["discarded_by_reason"]
    reasons[reason] = reasons.get(reason, 0) + 1


def _homeclass_authorizations(path, stats):
    authorized = set()
    for row in _read_rows(
        path, "homeclass", HOMECLASS_REQUIRED_HEADERS
    ):
        stats["rows_read"] += 1
        course_id = _parse_id(row.get("Odoo Subject ID"))
        moodle_ids = _parse_id_list(row.get("Moodle IDs List"))
        if not course_id or not moodle_ids:
            _discard_source(stats, "invalid_values")
            continue
        authorized.update((course_id, moodle_id) for moodle_id in moodle_ids)
        stats["rows_accepted"] += 1
    return authorized


def _online_inventory(path, stats):
    inventory = set()
    for row in _read_rows(path, "online", ONLINE_REQUIRED_HEADERS):
        stats["rows_read"] += 1
        moodle_id = _parse_id(row.get("ID Curso"))
        if not moodle_id:
            _discard_source(stats, "invalid_values")
            continue
        inventory.add(moodle_id)
        stats["rows_accepted"] += 1
    return inventory


def _skip(summary, reason):
    summary["skipped"] += 1
    skipped_by_reason = summary["skipped_by_reason"]
    skipped_by_reason[reason] = skipped_by_reason.get(reason, 0) + 1
    _discard_source(summary["sources"]["assignments"], reason)


def run_import(
    env, homeclass_csv_path, online_csv_path, assignments_csv_path
):
    """Upsert authorized course/subject Moodle routing from MacRoman CSVs."""
    course_map_model = env["irg.gradebook.moodle.course.map"]
    subject_map_model = env["irg.gradebook.moodle.map"]
    course_model = env["op.course"]
    subject_model = env["op.subject"]
    summary = {
        "course_maps": {"created": 0, "updated": 0},
        "subject_maps": {"created": 0, "updated": 0},
        "skipped": 0,
        "skipped_by_reason": {},
        "sources": {
            "homeclass": _source_stats(),
            "online": _source_stats(),
            "assignments": _source_stats(),
        },
    }
    homeclass_pairs = _homeclass_authorizations(
        homeclass_csv_path, summary["sources"]["homeclass"]
    )
    online_course_ids = _online_inventory(
        online_csv_path, summary["sources"]["online"]
    )
    processed_course_maps = {}

    for row in _read_rows(
        assignments_csv_path,
        "assignments",
        ASSIGNMENTS_REQUIRED_HEADERS,
    ):
        summary["sources"]["assignments"]["rows_read"] += 1
        course_id = _parse_id(row.get("Odoo Course ID"))
        moodle_course_id = _parse_id(row.get("Moodle Course ID"))
        subject_id = _parse_id(row.get("Odoo Subject ID"))
        activity_ids = _parse_id_list(row.get("Moodle IDs List"))
        moodle_course_name = (row.get("Curso Nombre") or "").strip()
        if not all(
            (course_id, moodle_course_id, subject_id, activity_ids, moodle_course_name)
        ):
            _skip(summary, "invalid_values")
            continue

        modality, _edition_year = parse_moodle_course_name(
            moodle_course_name
        )
        if not modality:
            _skip(summary, "invalid_online_marker")
            continue
        if modality == "online":
            is_authorized = moodle_course_id in online_course_ids
        else:
            is_authorized = (course_id, moodle_course_id) in homeclass_pairs
        if not is_authorized:
            _skip(summary, "unauthorized_course")
            continue

        course = course_model.browse(course_id).exists()
        subject = subject_model.browse(subject_id).exists()
        if not course or not subject:
            _skip(summary, "missing_odoo_record")
            continue
        if subject not in course.subject_ids:
            _skip(summary, "subject_not_in_course")
            continue

        course_key = (course_id, moodle_course_id)
        course_map = processed_course_maps.get(course_key)
        if not course_map:
            course_map = course_map_model.with_context(active_test=False).search(
                [
                    ("op_course_id", "=", course_id),
                    ("moodle_course_id", "=", moodle_course_id),
                ],
                limit=1,
            )
            course_values = {
                "moodle_course_name": moodle_course_name,
                "active": True,
            }
            if course_map:
                course_map.write(course_values)
                summary["course_maps"]["updated"] += 1
            else:
                course_map = course_map_model.create(
                    dict(
                        course_values,
                        op_course_id=course_id,
                        moodle_course_id=moodle_course_id,
                    )
                )
                summary["course_maps"]["created"] += 1
            processed_course_maps[course_key] = course_map

        activity_names = [
            name.strip()
            for name in (row.get("Moodle Names Found") or "").split("|")
        ]
        subject_map = subject_map_model.with_context(active_test=False).search(
            [
                ("op_subject_id", "=", subject_id),
                ("moodle_course_id", "=", moodle_course_id),
            ],
            limit=1,
        )
        subject_values = {
            "course_map_id": course_map.id,
            "moodle_course_name": moodle_course_name,
            "active": True,
        }
        if subject_map:
            subject_map.write(subject_values)
            summary["subject_maps"]["updated"] += 1
        else:
            subject_map = subject_map_model.create(
                dict(
                    subject_values,
                    op_subject_id=subject_id,
                    moodle_course_id=moodle_course_id,
                )
            )
            summary["subject_maps"]["created"] += 1

        existing_lines = {
            line.moodle_activity_id: line for line in subject_map.line_ids
        }
        for index, activity_id in enumerate(activity_ids):
            source_name = (
                activity_names[index]
                if index < len(activity_names)
                else ""
            )
            line = existing_lines.get(activity_id)
            if line:
                if source_name:
                    line.write({"name": source_name})
                continue
            env["irg.gradebook.moodle.map.line"].create(
                {
                    "map_id": subject_map.id,
                    "moodle_activity_id": activity_id,
                    "name": source_name or False,
                    "activity_type": "quiz",
                }
            )

        summary["sources"]["assignments"]["rows_accepted"] += 1

    return summary
