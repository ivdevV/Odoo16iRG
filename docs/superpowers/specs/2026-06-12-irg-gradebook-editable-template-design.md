# irg_gradebook_editable_template — Design

**Date:** 2026-06-12
**Status:** Approved

## Problem

`gradebook_id` (template de calificaciones) on `app.gradebook.student` is a stored
computed field without `readonly=False` or inverse
(`addons-extra/addons_uisep/isep_gradebook/models/app_gradebook_student.py:27`).
Odoo therefore renders it readonly everywhere — including Odoo Studio, which cannot
override field-level readonly.

The compute (`compute_gradebook_id`, depends on `course_id`) copies the template
from `course_id.gradebook_id`. When the course has no template, the field stays
empty and `state_to_done` cannot complete: the gradebook cannot be closed.

## Solution

New module `addons-extra/extrairg/irg_gradebook_editable_template` (project rule:
fixes ship as new modules under `extrairg`).

### Model — `models/app_gradebook_student.py`

Inherit `app.gradebook.student`:

- Redefine `gradebook_id` keeping compute, `store=True`, `tracking=True`, and add
  `readonly=False` so users can set it manually.
- Override `compute_gradebook_id` to preserve a manually set value:

```python
@api.depends('course_id')
def compute_gradebook_id(self):
    for rec in self:
        rec.gradebook_id = rec.gradebook_id or rec.course_id.gradebook_id
```

Without this, any recompute (e.g. course change) would wipe the manual value when
the course has no template.

### View — `views/app_gradebook_student_views.xml`

Inherit `isep_gradebook` form view for `app.gradebook.student`:

- `gradebook_id` gets `attrs="{'readonly': [('state','=','done')]}"` and
  `force_save="1"` — editable while the gradebook is open, locked once closed.

### Dependencies

`isep_gradebook`.

## Tests — `tests/test_editable_template.py`

1. Writing `gradebook_id` manually persists.
2. Recompute (course without template) does not clobber a manual value.
3. Course with template + empty field → compute fills it (existing behavior kept).

## Out of scope

- Subject-line `gradebook_id` (`app.gradebook.subject`): its compute already falls
  back to the student-level template, so closing works once the student field is set.
- No changes to `state_to_done` validation.
