# Spec: Auto-cierre de libreta (gradebook-auto-close)

## Contexto

- Libreta = `app.gradebook.student` (`addons-extra/addons_uisep/isep_gradebook/models/app_gradebook_student.py`)
- Líneas = `app.gradebook.subject`
- Notas = `app.gradebook.result` (entran manual o por sync Moodle)
- Botón "Cerrar libreta" = `state_to_done()` (valida cantidad de evaluaciones según template, lanza `UserError` si falta alguna)
- Reapertura ya existe: `state_to_in_progress()` y `action_draft()`

## Objetivo

Cerrar automáticamente la libreta (estado `done` / "Finalizado") cuando TODAS las líneas
tienen nota > 0 en: AVG Asignaciones, AVG Exámenes y Calificación final.
Algunas líneas no tienen AVG Asignaciones (ej. Prácticas, TFM): en esas se omite ese check.
La reapertura con los botones existentes debe seguir funcionando.

## Solución

Módulo nuevo `addons-extra/extrairg/irg_gradebook_auto_close` (no tocar `isep_gradebook`).
Depende de `isep_gradebook`.

## Tareas

### Tarea 1 — Condición de cierre en `app.gradebook.student`

Método `_irg_is_ready_to_close()`:

- `state == 'in_progress'` y al menos 1 línea.
- Para CADA línea de `gradebook_subject_ids`:
  - `final_subject_note > 0`
  - `point_average_exam > 0` **solo si** `show_exam`
  - `point_average_assignment > 0` **solo si** `show_assignment` (cubre asignaturas sin AVG Asignaciones)
- Si alguna línea falla → `False`.

**Criterio de aceptación**: unit test de la condición cubre los 3 casos (todo OK, línea a 0, línea sin asignaciones).

### Tarea 2 — Auto-cierre reutilizando lógica existente

Método `_irg_try_auto_close()`:

- Si `_irg_is_ready_to_close()` → llamar `state_to_done()` dentro de `try/except UserError`.
- Razón: `state_to_done()` ya valida cantidad de evaluaciones requeridas por template;
  si esa validación falla NO debe reventar el guardado de una nota — se captura,
  log warning, libreta queda `in_progress`.
- Reapertura intacta: al volver a "En proceso" no se re-cierra sola; solo se
  re-evalúa cuando cambia una nota.

**Criterio de aceptación**: con validación de template fallando, escribir nota no lanza error y estado queda `in_progress`.

### Tarea 3 — Trigger

Override `create/write/unlink` en `app.gradebook.result`:

- Tras `super()`, recolectar `gradebook_subject_id.gradebook_student_id` afectados
  y llamar `_irg_try_auto_close()`.
- `point_average_*` y `final_subject_note` son computes stored → asegurar recomputo
  antes del check (Odoo 16 resuelve dependencias al leer el campo).

**Criterio de aceptación**: escribir la última nota que completa la libreta dispara el cierre; cubre manual y sync.

### Tarea 4 — Tests (`tests/test_auto_close.py`)

1. Todas las líneas con exam avg, assignment avg y final > 0 → `done` al escribir última nota.
2. Una línea con final = 0 → sigue `in_progress`.
3. Línea sin asignaciones (`show_assignment=False`) pero exam y final > 0 → cierra igual.
4. Libreta reabierta manualmente → no se re-cierra hasta nuevo write de nota.
5. Validación de `state_to_done` falla (faltan evaluaciones del template) → no cierra, no lanza error.

**Criterio de aceptación**: 5/5 tests verdes en `test_irg_db`.

## Criterio de aceptación global

- Módulo instalado en `test_irg_db`, tests verdes.
- Flujo manual verificado: entrar última nota → libreta pasa a "Finalizado".
- Botones de reapertura operativos.

## Decisión abierta

Se usa `state_to_done()` (hereda validaciones del template) en vez de `state = 'done'` directo.
Si se prefiere cierre incondicional cuando notas > 0 aunque falten evaluaciones según
template, cambiar Tarea 2 a asignación directa.
