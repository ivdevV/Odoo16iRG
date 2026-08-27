# Contrato `irg.api.operation`

Modelo único escribible por el grupo de la fachada. Entrada MCP prevista: `create_record`. Aprobación: `action_approve` o meta-operación `irg_approve_operation`.

## Ciclo

```text
create(operation_code, environment, payload, idempotency_key)
        │
        ├─ kind=read  → result_snapshot, state=verified
        ├─ kind=meta  → aprueba/rechaza otra operación, state=verified
        └─ kind=write → before/proposed snapshots, state=preview
                              │
                              ├─ action_approve / irg_approve_operation
                              │     SELECT FOR UPDATE → savepoint → allowlist → verified
                              └─ action_reject / irg_reject_operation → rejected
```

## Idempotencia

Índice único `(requested_by, operation_code, idempotency_key)`.

- Misma clave y mismo hash de payload → se reutiliza el registro.
- Misma clave y hash distinto → error.

## Lecturas (fases 0–2)

| Código | Payload |
| --- | --- |
| `irg_list_academic_periods` | `limit`, `offset` |
| `irg_list_courses` | `limit`, `offset`, `name`, `code` |
| `irg_get_course_overview` | `course_id` |
| `irg_get_course_batches` | `course_id`, `limit`, `offset` |
| `irg_list_subjects` | `course_id`, `limit`, `offset` |
| `irg_get_course_structure` | `channel_id` |
| `irg_get_slide` | `slide_id` |
| `irg_get_admission_overview` | `admission_id` |
| `irg_get_admission_subject_openings` | `admission_id` |
| `irg_get_student_access` | `admission_id`, `partner_id` |
| `irg_get_student_academic_360` | `admission_id` |
| `irg_get_gradebook_summary` | `admission_id`, `partner_id` (si el modelo existe) |
| `irg_get_moodle_sync_status` | `course_id`, `admission_id` (si el modelo existe) |
| `irg_get_survey_structure` | `survey_id` |
| `irg_get_academic_incidents` | `admission_id`, `course_id` |

Paginación: `limit` por defecto 20, máximo 100. El serializer elimina secretos y binarios (`password`, `token`, `wstoken`, `datas`, …).

## Escrituras (fases 0–2)

| Código | Payload | Efecto |
| --- | --- | --- |
| `irg_create_slide_draft` | `channel_id`, `name`, `html_content`, `sequence`, `irg_section_id`, `is_published` | Crea artículo no publicado. `is_published` del cliente se ignora. |
| `irg_update_slide_draft` | `slide_id`, `name`, `html_content`, `sequence`, `irg_section_id` | Solo slides artículo no publicados |
| `irg_create_course_section` | `channel_id`, `name`, `sequence` | Sección `irg.slide.section` |
| `irg_reorder_course_section` | `channel_id`, `section_ids` | Reordena |
| `irg_publish_slide` | `slide_id` | Publica un slide ya revisado |
| `irg_unpublish_slide` | `slide_id` | Despublica |

Apply usa allowlist de campos ORM. Create de slide fuerza `is_published=False` y `slide_category=article`.

## Meta

| Código | Payload |
| --- | --- |
| `irg_approve_operation` | `operation_id` |
| `irg_reject_operation` | `operation_id` |

Las meta-operaciones se aplican en el mismo `create` (no requieren una segunda aprobación) para evitar bucles.

## Seguridad

- Grupo `irg_business_api.group_irg_business_api_user`. Record rule: el usuario ve sus operaciones de su compañía; `base.group_system` ve todas.
- ACL: create/read/write, `unlink=0`. `unlink()` y `write()` del modelo levantan `AccessError`.
- Mutaciones internas: `super().write()`, nunca un flag de contexto RPC.
- `environment=production` rechazado.
- `sudo()` solo después de comprobar grupo + código de operación.
