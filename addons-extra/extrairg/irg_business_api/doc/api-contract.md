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

## Fases 3–6

Los `irg_preview_*` son lecturas. Los `irg_apply_*` son escrituras (preview → approve).

| Código | Payload | Notas |
| --- | --- | --- |
| `irg_preview_online_clone` / `irg_apply_online_clone` | `channel_id` (HomeClass) | Llama a `action_copy_homeclass_to_online`. No copiar memberships. Rechaza si Online ya tiene slides. |
| `irg_preview_content_reconciliation` / `irg_apply_content_reconciliation` | `channel_id` | Apply solo si Online está vacío (mismo bootstrap). |
| `irg_preview_subject_opening` / `irg_apply_subject_opening` | `admission_id` | `_irg_generate_online_subject_openings` |
| `irg_preview_access_reconciliation` / `irg_apply_access_reconciliation` | `admission_id` | `_irg_sync_online_channel_partners` + guardarraíl 30 % |
| `irg_preview_enrollment` / `irg_apply_enrollment` | `admission_id` | Solo `enroll_student` desde `confirm`. Si ya está `done`, error. |
| `irg_preview_withdrawal` / `irg_apply_withdrawal` | `admission_id` | Apply **rechazado** (`action_down` no se expone). |
| `irg_get_access_exceptions` | `admission_id` | Lectura |
| `irg_get_batch_schedule` | `batch_id` | Lectura |
| `irg_preview_batch_schedule_sync` / `irg_apply_batch_schedule_sync` | `batch_id`, `lines` | `lines`: `{subject_id, date_from, date_to}` |
| `irg_preview_subject_precedence` / `irg_get_student_subject_eligibility` | `subject_id`, `admission_id` | `can_be_taken` |
| `irg_preview_moodle_course_mapping` / `irg_apply_moodle_course_mapping` | `maps` | Mapas explícitos `{moodle_course_id, subject_id}`. No importa el catálogo Moodle. |
| `irg_preview_moodle_grade_sync` / `irg_apply_moodle_grade_sync` | `course_id`, `admission_id` | `_sync_moodle_grades`; no devuelve tokens. |
| `irg_confirm_moodle_student_match` | `grade_id`, `student_id` | Emparejamiento manual |
| `irg_get_student_grade_evidence` | `admission_id`, `subject_id` | Resultados fuente del gradebook |
| `irg_create_survey_draft` / `irg_update_survey_draft` | `title` / `survey_id`, `title` | Encuesta no publicada |
| `irg_preview_auto_score` / `irg_apply_auto_score` | `survey_id` | `action_auto_score_quiz` |
| `irg_preview_regrade_attempt` / `irg_apply_regrade_attempt` | `user_input_id` | Un intento |
| `irg_preview_feedback_import` / `irg_apply_feedback_import` | `survey_id`, `txt_content` | Wizard TXT oficial |
| `irg_get_attachment_metadata` | `attachment_id` | Sin binario |
| `irg_upload_private_attachment` | `res_model`, `res_id`, `name`, `mimetype`, `file_b64` | `public=False`, máx. 32 KiB |

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
