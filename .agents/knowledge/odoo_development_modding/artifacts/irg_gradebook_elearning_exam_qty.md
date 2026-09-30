# Recuento de exámenes e-learning por asignatura y lote

Fecha: 2026-09-18

Módulo: `irg_gradebook_elearning_exam_qty`

## Decisión reutilizable

La cantidad de exámenes de una línea de libreta no debe vivir como entero en
`op.batch` ni en el catálogo `op.subject`. Se detecta en el canal e-learning
de **esa** asignatura (`op.subject.slide_channel_id`) filtrando
`slide.allowed_batch_ids` contra `app.gradebook.student.batch_id`.

Vacío en `allowed_batch_ids` = sin requisito (cuenta para todos). Lista
informada = solo esos lotes. N es por línea: la misma libreta puede exigir 3
en una asignatura y 2 en otra.

Sustituir `exam.qty` en `_get_gradebook_info` después de `super()`, solo si
N > 0 y la libreta no está `done`.

## Motivos

- Alumnos viejos y nuevos comparten `op.subject` y a menudo el mismo canal.
- El aislamiento ya está en campus (lotes permitidos por slide).

## Gotchas

- No usar `slide.is_user_allowed_by_batch(user)`: busca la matrícula campus
  del usuario actual (admin en tests/backend), no el lote de la admisión.
- No filtrar por `scheduled_date` si el cierre no debe ocurrir con el primer
  examen mientras el segundo aún no es visible.
- `__init__.py` raíz del addon no debe importar `tests`.
- `auto_install` False.
