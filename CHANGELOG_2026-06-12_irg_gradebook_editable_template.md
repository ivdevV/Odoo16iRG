# CHANGELOG — 2026-06-12 — irg_gradebook_editable_template

## Nuevo módulo: `addons-extra/extrairg/irg_gradebook_editable_template` (16.0.1.0.0)

### Problema

El campo `gradebook_id` (Calificaciones template) de la libreta
(`app.gradebook.student`) era de solo lectura: campo computado sin
`readonly=False`. Si el curso no tenía template asignado, el campo quedaba
vacío y la libreta no se podía cerrar. Odoo Studio no podía hacerlo editable.

### Cambios

- `gradebook_id` redefinido con `readonly=False` → editable en el formulario.
- Compute conserva el valor manual; solo rellena desde el curso si está vacío.
- Vista heredada: campo bloqueado cuando la libreta está en estado `done`.

### Pruebas

- 3 tests unitarios (TDD), `0 failed, 0 error(s)` en Odoo local
  (`docker-compose.local.yml`, DB limpia `test_gbedit`).

### Despliegue

- Instalar módulo `irg_gradebook_editable_template` (sin migración de datos).
