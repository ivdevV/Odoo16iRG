# Design — irg_business_api (entrega fases 0–2)

**Fecha:** 2026-08-27
**Módulo:** `addons-extra/extrairg/irg_business_api`

## Arquitectura

```text
Lisa/MCP (create_record / action_approve)
        ↓
irg.api.operation  (ACL + record rules + allowlist)
        ↓
servicios internos (academic / elearning / access / gradebook / moodle)
        ↓
modelos iRG existentes (sin modificar)
```

El contrato funcional no es `execute_kw` genérico. El único modelo escribible por el grupo de la fachada es `irg.api.operation`.

## Modelo `irg.api.operation`

Campos de cliente: `operation_code`, `environment`, `request_payload` (JSON), `idempotency_key`, `target_model`/`target_id` informativos.

Campos de servidor (no aceptados en create/write externo): `request_hash`, `state`, snapshots, `changed_fields`, `warnings`, `errors`, actores y timestamps, `audit_reference`, `company_id`, `requested_by`.

Estados: `preview`, `awaiting_approval`, `applied`, `rejected`, `failed`, `verified`.

Ciclo de escritura: validar → preview → `action_approve` → releer `write_date` → savepoint → escribir allowlist → releer → verificar invariantes → `verified`.

## Operaciones de esta entrega

Lectura: periodos, cursos, overview de curso, lotes, asignaturas, estructura, slide, admisión, aperturas, acceso Campus, 360 mínimo, gradebook (si el modelo existe), Moodle (si existe), encuesta, incidencias (unmatched Moodle / aperturas incoherentes).

Escritura: crear/actualizar slide artículo no publicado, crear/reordenar sección, publicar y despublicar (confirmación separada).

## Seguridad

- Grupo `group_irg_business_api_user`, distinto de administradores.
- ACL: create/read/write sobre el modelo de operación; `unlink` denegado.
- Record rule: el usuario del grupo ve sus operaciones de su compañía; `base.group_system` ve todas.
- `sudo()` documentado y posterior a la autorización del grupo.
- Serializer con denylist de secretos/binarios; email/nombre solo en lecturas de alumno.
- Límite de payload 64 KiB antes de parsear; HTML 32 KiB; página máxima 100.
- Entorno `production` rechazado.
- Métodos de servicio con prefijo `_irg_` no invocables por RPC genérico.

## Concurrencia e idempotencia

Índice único `(requested_by, operation_code, idempotency_key)`. Misma clave y hash: se reutiliza el registro. Misma clave y hash distinto: error. Entre preview y apply se compara `write_date` del objetivo.
