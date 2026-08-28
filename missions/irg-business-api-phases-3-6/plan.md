# Plan — irg-business-api-phases-3-6

Fuente: plan técnico `irg_business_api` (2026-08-27) fases 3–6.
Fachada existente: `addons-extra/extrairg/irg_business_api` (fases 0–2 en `Dev_iRG`).

## Clasificación

- Misión: `full`
- Tier: `complex` (clonación, accesos, matrícula, Moodle, encuestas, adjuntos)
- Security Advisor: **obligatorio** (autenticación, concurrencia, datos académicos, matrícula)
- E2E TestSprite: **skipped** si el diff no toca vistas/XML/static/HTTP (solo Python de operaciones). Obligatorio si se modifica `views/`.

## Objetivo

Exponer el resto del catálogo del plan técnico como operaciones allowlist de `irg.api.operation`, **reutilizando** la lógica oficial (no reimplementar bootstrap, enroll ni sync Moodle). Cero cambios en módulos existentes.

## Knowledge consultada

- `irg_business_api_command_facade.md` (`write()` cerrado, `super().write()`, `self.sudo().env`)
- `irg_auto_enroll_cron_robust.md` (guardarraíl 30 %, no `unlink` como corrección propia)
- `irg_gradebook_moodle_course_activity_routing.md` (no tokens, no mezclar ediciones)
- Bootstrap HomeClass→Online: `action_copy_homeclass_to_online` en `irg_course_convocatorias_v2`

## Decisiones cerradas

1. Clonación: `irg_apply_online_clone` llama a `action_copy_homeclass_to_online` sobre el canal HomeClass. No es un `create` de `slide.channel` + `op.subject`.
2. Preview `irg_preview_*` son lecturas (ejecutan en el `create`). `irg_apply_*` son escrituras (preview → approve).
3. `irg_apply_withdrawal` **no** llama a `action_down()` (cancela facturas y cambia estado). Preview informa efectos; apply se rechaza.
4. Moodle: mapas explícitos en payload; sync de notas solo vía `_sync_moodle_grades` (sin devolver credenciales). Import masivo del catálogo Moodle no se dispara desde Lisa.
5. Adjuntos: privados, tamaño acotado; nunca `public=True`.
6. Entorno `production` sigue rechazado. Lisa MCP no se cambia en este diff.

## Criterios de aceptación

- Aprobar `irg_apply_online_clone` sobre un canal HomeClass con contenido copia slides, secciones y quizzes al canal Online y no copia memberships.
- Si el Online ya tiene slides, no duplica (misma guarda que la UI).
- Aperturas y accesos delegan en `_irg_generate_online_subject_openings` / `_irg_sync_online_channel_partners` con guardarraíl 30 %.
- Matrícula solo vía `enroll_student` si la admisión no está ya `done`.
- Tests Odoo `/irg_business_api` en verde.

## Fuera de alcance

- Cambiar la allowlist MCP de Lisa.
- Adjuntos públicos, borrar intentos, `action_down`, SQL, `call_model_method`.
