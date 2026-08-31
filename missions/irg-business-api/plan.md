# Plan — irg-business-api

Fuente aprobada: plan técnico `irg_business_api` (2026-08-27).
Spec: `docs/superpowers/specs/2026-08-27-irg-business-api-design.md`
Micro-spec: `doc/micro-specs/2026-08-27-irg_business_api.md`

## Clasificación

- Misión: `full` (módulo nuevo, comportamiento de producto, seguridad, datos académicos, concurrencia)
- Tier: `complex` (cross-module, ACL, idempotencia, snapshots, escrituras eLearning)
- Capacidad requerida: máxima de razonamiento disponible
- Security Advisor: **obligatorio** antes de implementar (autenticación de operaciones, concurrencia, datos)
- E2E TestSprite: **obligatorio** — el diff crea `views/api_operation_views.xml`

## Objetivo de esta entrega

Fases 0, 1 y 2 del plan técnico: fachada `irg_business_api` con modelo de comandos `irg.api.operation`, lecturas académicas paginadas y escrituras de slide/sección en borrador. No se implementan clonación, aperturas/matrícula, sync Moodle de escritura, encuestas de escritura ni adjuntos públicos.

## Knowledge consultada

- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
- `irg_auto_enroll_cron_robust.md` (savepoints, duplicados activos, no `unlink` como corrección)
- `irg_gradebook_moodle_course_activity_routing.md` (no mezclar ediciones; no devolver tokens)
- `irg_auto_enroll_cron_routing_fix.md`
- Preparación Lisa: allowlist MCP con lecturas + `create_record`/`update_record`/`post_message`; `delete_record` y `call_model_method` excluidos. `update_record` obliga a que `write()` del modelo de comandos rechace campos de estado.

## Decisiones cerradas

1. Addon nuevo en `addons-extra/extrairg/irg_business_api`. Cero cambios en módulos existentes.
2. Entrada MCP: `create` de `irg.api.operation`. Aprobación: `action_approve()`. Sin controladores HTTP en esta entrega.
3. `create`/`write` ignoran y rechazan `state`, snapshots, hashes, `requested_by` y marcas temporales enviadas por el cliente.
4. `sudo()` solo tras comprobar `group_irg_business_api_user` (o `base.group_system`) y el código de operación; cada uso lleva comentario y test.
5. `environment` admite `test` y `beta`. `production` se rechaza.
6. Gradebook y Moodle se leen si el modelo está instalado; no se declaran como `depends` hasta que haya escrituras de esos contratos.
7. Publicar/despublicar son operaciones distintas y nunca ocurren al crear un borrador.
8. Lisa no forma parte de este diff; la fachada es el contrato que sustituirá el CRUD genérico más adelante.

## Dependencias del manifest

```python
[
    'irg_course_convocatorias_v2',
    'irg_online_subject_opening',
    'openeducat_admission',
]
```

El resto llega por transitorias (`website_slides`, `isep_elearning_custom`, `irg_elearning_editable_sections`, `isep_subject_precedence`, `irg_op_course_modality`).

## Criterios de aceptación

- Instalación en base de pruebas sin modificar nativos.
- Lecturas con paginación, campos reales y sin secretos.
- `irg_create_slide_draft` crea un artículo no publicado en el canal indicado.
- Misma `idempotency_key` + mismo hash no duplica; misma clave + hash distinto se rechaza.
- Publicación, clonación, accesos, matrículas, notas, recalificación y adjuntos públicos no se ejecutan por defecto.
- Cada escritura aprobada deja preview, auditoría y lectura posterior.
- Usuario sin el grupo no puede crear ni aprobar operaciones; `write` directo no puede forjar `state=applied`.

## Pruebas

- `test_api_read_contract.py`
- `test_slide_draft_operations.py`
- `test_idempotency_and_concurrency.py`
- `test_access_permissions.py`

Runtime: `docker-compose.local.yml` + overlay del worktree. Base desechable. Cleanup y restauración del servicio compartido.

## Fuera de alcance (fases 3–6)

Clonación Online, reconciliación de contenido/acceso, matrícula/baja, sync de calendario, mapeo/notas Moodle de escritura, encuestas, recalificación, importación TXT, subida de adjuntos.
