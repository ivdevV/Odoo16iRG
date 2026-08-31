# Micro-spec: IRG Business API

## 1. Título

Fachada de negocio `irg_business_api` (lecturas académicas y borradores eLearning).

## 2. Resumen objetivo

Crear un módulo extra con un modelo de comandos cerrado para que Lisa consulte datos académicos y cree/edite slides y secciones en borrador, sin ORM arbitrario.

## 3. Motivo

El MCP genérico no es un contrato funcional. Exponer `create_record`/`update_record` sobre modelos académicos es inaceptable para flujos nuevos. Un addon propio con ACL, allowlist e idempotencia evita tocar nativos y concentra la auditoría.

## 4. Alcance exacto

- Modelos nuevos: `irg.api.operation`.
- Vistas: árbol/formulario/búsqueda del modelo de operación.
- Seguridad: grupo, ACL, record rules.
- Servicios internos de lectura y de slide/sección.
- Tests Odoo etiquetados `/irg_business_api`.
- Fuera: HTTP público, clonación, matrícula, sync Moodle de escritura, encuestas de escritura, adjuntos públicos, `unlink` académico.

## 5. Diseño técnico

- `create()` normaliza payload, calcula hash, fija `requested_by` y ejecuta lecturas o deja preview de escritura.
- `write()` externo no puede cambiar estado ni snapshots.
- `action_approve()` / `action_reject()` son los únicos transitores públicos, con guarda de grupo y de estado.
- Slides se crean con `slide_category='article'` e `is_published=False`.
- `sudo()` solo en lecturas/escrituras académicas autorizadas por la operación.

## 6. Dependencias

`irg_course_convocatorias_v2`, `irg_online_subject_opening`, `openeducat_admission`.

## 7. Backwards-compatibility

Addon nuevo. No migra ni borra datos históricos. Desinstalar retira el grupo/ACL; no deshace escrituras aplicadas.

## 8. Casos de prueba / aceptación

Ver `missions/irg-business-api/plan.md` sección criterios y tests.

## 9. Rollback

Desinstalar `irg_business_api` en ventana controlada. No borrar operaciones históricas como corrección. Restaurar allowlist MCP anterior si se retira la fachada.

## 10. Estimación y responsable

Entrega fases 0–2. Responsable de implementación: misión `irg-business-api`. Consumidor: Lisa / MCP Odoo BETA, sin cambiar su configuración en este diff.
