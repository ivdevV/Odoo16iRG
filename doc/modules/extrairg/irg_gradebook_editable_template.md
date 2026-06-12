# irg_gradebook_editable_template

**Versión:** 16.0.1.0.0
**Dependencias:** `isep_gradebook`

## Problema

En `app.gradebook.student` (libreta de calificaciones), el campo `gradebook_id`
(template de calificaciones) es un campo computado almacenado sin
`readonly=False` ni inverse, definido en
`addons-extra/addons_uisep/isep_gradebook/models/app_gradebook_student.py`.
Odoo lo bloquea en todas las vistas — Odoo Studio tampoco puede hacerlo editable
porque el readonly es a nivel de campo.

El compute copia el template desde `course_id.gradebook_id`. Si el curso no
tiene template, el campo queda vacío y la libreta no se puede cerrar
(`state_to_done` lo exige).

## Solución

- Redefine `gradebook_id` con `readonly=False`: editable en el formulario,
  manteniendo compute, `store=True` y `tracking`.
- Override de `compute_gradebook_id`: conserva el valor puesto a mano; solo
  rellena desde el curso cuando el campo está vacío. Sin esto, cualquier
  recálculo borraría la selección manual.
- Vista heredada: `gradebook_id` queda readonly cuando la libreta está en
  estado `done` (Finalizado), con `force_save="1"`.

## Uso

1. Abrir la libreta (Libretas → registro en estado "En proceso").
2. Seleccionar manualmente el "Calificaciones template".
3. Cerrar la libreta con el botón "Cerrar Libreta".

Con la libreta cerrada el campo vuelve a ser de solo lectura.

## Tests

`tests/test_editable_template.py` (3 tests):

- `test_field_is_editable`: el campo tiene `readonly=False`.
- `test_manual_value_preserved_on_recompute`: el valor manual sobrevive al
  recálculo cuando el curso no tiene template.
- `test_course_template_fills_empty`: el compute sigue copiando el template del
  curso cuando el campo está vacío (regresión del comportamiento original).

Ejecutados en Odoo local (`docker-compose.local.yml`, DB `test_gbedit`):
`0 failed, 0 error(s) of 3 tests`.

## Limitaciones conocidas

- El `gradebook_id` de las líneas de asignatura (`app.gradebook.subject`) no se
  modifica: su compute ya usa como fallback el template de la libreta, por lo
  que basta con fijar el de la cabecera.
- Si la libreta ya tiene template (manual o del curso), cambiar el curso no lo
  sobrescribe: el valor existente siempre gana.
