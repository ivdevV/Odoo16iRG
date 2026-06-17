# Mision: irg_diplomado_course_duration

## Alcance

Anadir campos configurables en el curso para que los diplomas de diplomado no impriman `0 horas` y puedan mostrar tambien los ECTS configurados.

## Clasificacion de complejidad

Tier: `standard`.

Justificacion: se crea un modulo nuevo por herencia, con campos en `op.course`, vista heredada, extension del wizard de generacion y adaptacion del portal propio para usar los valores si existen. No toca autenticacion, migraciones, secretos ni datos historicos.

## Knowledge base consultada

- `.agents/knowledge/odoo_development_modding/artifacts/diplomado_report_layout.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_diplomado_portal_request.md`

## Plan

1. Crear modulo `irg_generacion_diplomados_course_duration`.
2. Extender `op.course` con `irg_diplomado_duration_hours` y `irg_diplomado_duration_ects`.
3. Inyectar campos en la pagina `Asignaturas Diplomado` del formulario de curso.
4. Extender `irg.diplomado.wizard._onchange_course_id()` para precargar Horas y ECTS desde el curso.
5. Actualizar la descarga directa del portal para pasar esos valores al `irg.diplomado.registry` cuando los campos existan.
6. Anadir tests para campos y wizard.
7. Validar con `docker-compose.local.yml`.
