# Patron: Horas y ECTS de diplomados desde el curso

Fecha: 2026-06-16

Modulo: `irg_generacion_diplomados_course_duration`

## Decision reutilizable

Las horas y ECTS que se imprimen en un diploma de diplomado deben configurarse en `op.course`, no introducirse manualmente en cada emision.

Campos usados:

- `op.course.irg_diplomado_duration_hours`
- `op.course.irg_diplomado_duration_ects`

## Integracion

- El wizard `irg.diplomado.wizard` precarga `duration_hours` y `duration_ects` desde el curso en `_onchange_course_id()`.
- El portal `irg_diplomado_portal_request` copia esos valores al `irg.diplomado.registry` antes de generar el PDF.
- El PDF ya usa `duration_hours` y `duration_ects` desde el registro, por lo que la correccion consiste en poblarlos bien antes de llamar a `action_reprint()`.

## Gotchas

- No modificar directamente `irg_generacion_diplomados`; crear un modulo por herencia para campos y vista.
- Si el portal crea el registro sin copiar estos campos, `action_reprint()` seguira imprimiendo `0 horas`.
