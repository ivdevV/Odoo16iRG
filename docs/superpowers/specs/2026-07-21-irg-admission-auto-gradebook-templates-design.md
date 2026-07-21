# Design — Auto gradebook templates on enrollment

## Problem

`irg_admission_auto_gradebook` creates `app.gradebook.student` and subject lines on
`enroll_student`, but does not assign `gradebook_id`. The field only fills when
`course.gradebook_id` is set (via `irg_gradebook_editable_template` compute).
Masters and diplomados without a course template remain without a grading template.

## Decisions

1. **Precedence:** use `course.gradebook_id` when present; otherwise apply a
   canonical template by course kind.
2. **Canonical diplomado:** `irg_diploma_gradebook_template_weighting.gradebook_diploma_exam_50_50`
   (`Diplomado - Solo examen - Ponderación 50/50`).
3. **Canonical master:** xml_id
   `irg_admission_auto_gradebook_templates.gradebook_master_solo_examen`
   (`Solo Examen`); if missing, search `app.gradebook` by exact name `Solo Examen`.
4. **Other courses** without `course.gradebook_id`: leave `gradebook_id` empty.
5. **Master detection:** `course_type_id` name/code **or** unequivocal course name
   (`Máster`/`Master` at start or after ` - `), with accent-normalized text.
6. **Diplomado detection:** reuse `app.gradebook.student._is_diplomado_course()`
   (including beta name fallback when that module is installed).
7. **Scope of write:** only header `app.gradebook.student.gradebook_id`; do not
   force subject-line templates.
8. **Delivery:** new bridge module (do not edit existing addons).

## Architecture

New module `irg_admission_auto_gradebook_templates`:

- Depends on `irg_admission_auto_gradebook`, `irg_gradebook_editable_template`,
  `irg_diploma_gradebook_template_weighting` (and preferably
  `irg_diploma_gradebook_beta_course_detection` for robust diplomado names).
- Overrides `op.admission.enroll_student`: call `super()`, then for each admission
  in `done` with an existing student gradebook whose `gradebook_id` is empty,
  resolve and `write` the canonical template.
- Provides XML data for master `Solo Examen` (exam 100%, standard mode).
- Idempotent: never overwrites a non-empty `gradebook_id`.

## Tests

- Course with `gradebook_id` → libreta keeps course template.
- Diplomado without course template → diploma 50/50 canonical.
- Master without course template (type or name) → Solo Examen.
- Other course without template → remains empty.
- Subject lines are not force-written.
