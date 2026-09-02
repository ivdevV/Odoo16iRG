# Progress — irg-practice-modality-elearning

Coder terminó la implementación TDD de ambos módulos. Sin commit.

## Módulo A `irg_student_course_practice_modality`

- Campo `op.student.course.irg_practice_center_type_id`.
- Sync desde `practice.request` en `approved`/`progress`/`end`.
- Helper `op.student.irg_get_practice_center_type(course)`.
- Vistas backend, campus y portal educativo.

## Módulo B `irg_practice_slide_restrictions`

- Campo `slide.slide.irg_required_practice_type`.
- `is_user_allowed_by_practice_type`, GET `/slides/slide/<id>`, QWeb (mantiene condiciones de lote).
- Página «Contenido Bloqueado».

## Tests

18 tests, 0 failed, 0 error. Ver `artifacts/green-modules.txt`.
