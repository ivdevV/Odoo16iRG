# Diseño: qty de exámenes desde e-learning (por asignatura y lote)

Fecha: 2026-09-18

Módulo: `irg_gradebook_elearning_exam_qty`

## Objetivo

Que el denominador de `AVG Exámenes => [n de N]` y el cierre de la libreta usen
**N detectado en campus**: cuántos exámenes hay en el canal e-learning de **esa
asignatura** para los que el **lote de la libreta** cumple el requisito de lote.

No hay un entero en `op.batch`. Un mismo lote (y una misma libreta) puede tener
una asignatura con 3 exámenes y otra con 2.

## Por qué no va en el lote ni en el catálogo de asignatura

`qty` vive hoy en `app.gradebook.template.line` (casi siempre 1). La línea de
libreta (`app.gradebook.subject`) toma primero `op.subject.gradebook_id`. Cambiar
ese template o un campo en el lote afectaría a todas las asignaturas por igual y
a alumnos viejos y nuevos.

Los exámenes nuevos se publican en el mismo `slide.channel` de la asignatura. El
aislamiento ya existe en e-learning: `slide.slide.allowed_batch_ids` («Lotes
Permitidos» de `irg_batch_slide_restrictions`). Si el m2m tiene lotes, solo esos
lotes acceden; si está vacío, no hay requisito y el contenido vale para todos.

## Detección

Por cada línea `app.gradebook.subject` (no por cabecera ni por lote):

1. Canal: `op_subject_id.slide_channel_id`.
2. Recorrer `slide_ids` del canal (no secciones: `is_category` falso).
3. Candidato a examen: `is_published`, `survey_id` informado,
   `survey_id.survey_type == 'exam'`.
4. Requisito de lote (misma semántica que el acceso, pero con el lote de la
   libreta, no con el usuario admin del ORM):
   - `allowed_batch_ids` vacío → no hay requisito → **cuenta** para cualquier lote;
   - `allowed_batch_ids` informado → **cuenta** solo si
     `gradebook_student_id.batch_id` está en esa lista.
5. **No** filtrar por `scheduled_date`. Un examen aún no abrible **sí** entra en N.
6. N = número de `survey_id` **únicos** (dos slides con la misma encuesta = 1).

No contar asignaciones, borradores, ni slides cuyo requisito de lote excluye el
lote de la libreta.

Si N = 0 (sin canal, sin exámenes Odoo, Moodle-only): dejar el `qty` de la
plantilla (`super()`).

```text
misma libreta / mismo lote
  asignatura A (canal A): 3 slides exam permitidos para el lote → N=3
  asignatura B (canal B): 2 slides exam permitidos para el lote → N=2
```

No se usa `slide.is_user_allowed_by_batch(user)`: busca la matrícula campus del
usuario actual (`slide.channel.partner`). El recuento debe usar
`app.gradebook.student.batch_id` (related de la admisión).

## Diseño del addon

Addon nuevo en `addons-extra/extrairg/`, prefijo `irg_`, `auto_install` False.

Dependencias: `isep_gradebook`, `irg_batch_slide_restrictions`.
`isep_gradebook` ya arrastra `isep_elearning_custom` (`slide_channel_id`) e
`isep_survey` / `website_slides_survey` (`survey_id`, `survey_type`).

No se editan módulos existentes. No hay campo en `op.batch`, ni entero en la
cabecera de la libreta, ni vistas, cron, controladores o parámetros en v1.

Hereda `app.gradebook.subject`:

- `_irg_elearning_exam_qty()` → `int` (0 = no sustituir).
- `_irg_slide_allows_gradebook_batch(slide, batch)` → `bool`.
- `_get_gradebook_info(rec)` llama a `super()`, y si la libreta no está `done` y
  N > 0 sustituye `gradebook['exam']['qty']`. Pesos y demás tipos no se tocan.

Libreta `done`: no sustituir (un examen publicado después no reabre requisitos).
Libreta `in_progress`: recuento vivo al llamar `_get_gradebook_info` (cierre y
promedios). `info_exam` es computed stored: se refresca cuando el compute de
promedios vuelve a correr (p. ej. al guardar un resultado).

## Regla operativa

Al publicar un examen extra en un canal compartido, poner en `allowed_batch_ids`
los lotes nuevos. Si se deja vacío, las libretas `in_progress` de lotes antiguos
pasarían a exigir ese examen.

## Límites

- Wizard Moodle (`qty == 1`) no se cambia. Sin slides de examen Odoo, fallback a
  plantilla.
- No se usa `active_lib` (es del cron de asignaciones con IA).
- Sin override manual en v1.

## Pruebas de aceptación

- Un examen publicado sin requisito de lote: N=1; cierra con 1 resultado.
- Misma libreta: asignatura A con 3 exámenes del lote y B con 2 → N 3 y 2;
  no cierra hasta cumplir cada línea.
- Segundo examen con `allowed_batch_ids` = lote nuevo: la libreta del lote nuevo
  exige 2; la del lote viejo sigue en 1.
- `scheduled_date` futura: el lote permitido ya exige ese examen.
- Slide no publicado, tipo assignment o el mismo `survey_id` duplicado: no
  inflan N de más.
- Sin canal: se conserva el qty de plantilla.
- Libreta `done` con N=1: añadir un examen al canal no cambia el denominador
  almacenado ni el resultado de `_get_gradebook_info` (no sustituye).
