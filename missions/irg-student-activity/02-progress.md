# Progress — irg-student-activity

## Task 1: Scaffold + assembler contract (empty / access)

**Status:** Implemented (pending Validator)

### Done
- Added module scaffold under `addons-extra/extrairg/irg_student_activity/` (manifest, models, security, stub view, tests, README, csv_export stub).
- TDD: RED (module ignored without manifest) → GREEN (`-i irg_student_activity`, 2 tests pass).
- Evidence: `missions/irg-student-activity/artifacts/task-1-red.txt`, `task-1-green.txt`.
- Report: `.superpowers/sdd/task-1-report.md`.

## Task 2: Campus events in assembler

**Status:** Implemented (pending Validator)

### Done
- TDD: RED (`test_campus_completed_appears_and_skips_not_started`, 1 failed) → GREEN (3 tests pass).
- `_campus_rows`, `_batch_code_for_channel`, sort/limit in `activity_assemble.py`.
- `_activity_event_rows` uses `sudo()` after assert for slide.partner read access.
- Report: `.superpowers/sdd/task-2-report.md`; evidence: `artifacts/task-2-green.txt`.

## Task 3: Evaluation events + merge + limit

**Status:** Test fix implemented (pending Validator)

### Done
- TDD: added `test_evaluation_row_and_order_with_campus`, `test_activity_limit_500` (monkeypatch 505 rows).
- `_evaluation_rows`, merge campus+evaluation, `_activity_sort_key` with `datetime.min`, limit 500.
- `_slide_in_published_domain` wires `_published_slide_domain` for campus rows.
- Report: `.superpowers/sdd/task-3-report.md`.
- **Fix (Task 3 test):** `test_evaluation_row_and_order_with_campus` — create `survey.survey` before certification slide; pass `survey_id` to `_create_slide`; SQL + `invalidate_recordset` so evaluation `end_datetime` sorts after campus (stable sort tie-break).
- Docker GREEN: `artifacts/task-3-green.txt` — `0 failed, 0 error(s) of 5 tests`.

## Task 4: Computed lines UI + export CSV

**Status:** Implemented (pending Validator)

### Done
- TDD: RED (`artifacts/task-4-red.txt`) → GREEN (`artifacts/task-4-green.txt`, 8 tests pass).
- `_compute_activity_line_ids` via `_activity_event_rows()` with `AccessError` → empty lines.
- `build_activity_csv`, `action_export_activity_csv` (attachment + act_url).
- Actividad tab: tree readonly + Exportar CSV button.
- Report: `.superpowers/sdd/task-4-report.md`.

## Task 5: README + mission execution stub

**Status:** Implemented (pending Validator)

### Done
- README alineado con el brief (uso, permisos Facultad, fuera de alcance).
- `execution.md`: comando `docker compose run`, tabla RED/GREEN con rutas
  bajo `artifacts/`, nota snapshot Debian tras apt 404 en build.
- Report: `.superpowers/sdd/task-5-report.md`.

### Pending (later tasks)
- Review, Validación, E2E (orquestador / validador).

### Notes
- Commit skipped (user did not authorize).
- Tests run via `docker compose run --rm --no-deps odoo_local` because `odoo_local` cannot bind 8069 (another container uses the port).

## Final-fix r2 (post final-review-r2)

**Status:** Implemented (pending Validator)

### Done
- I1-r2: `_slide_is_published` — removed `slide.exists()`; truthy slide + `channel_id` + field checks only.
- I2-r2: `action_export_activity_csv` unlinks prior user CSV attachments (`actividad_%.csv`, no res link) before create; test `test_export_csv_replaces_previous_user_attachments`.
- N1: compute unlink scoped to `student_id` + `create_uid = env.user`.
- N2: README note — tab may stay empty until partner saved when editing.
- Docker verify: `artifacts/final-fix-r2-green.txt` — `0 failed, 0 error(s) of 11 tests`.
- Report append: `.superpowers/sdd/task-final-fix-report.md`.

### Pending
- Review, Validación (orquestador / validador).
