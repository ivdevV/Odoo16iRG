# Mission Plan — irg-practice-request-online-types

## Fuente y objetivo

- Spec: `docs/superpowers/specs/2026-09-02-practice-request-online-types-design.md`
- Plan: `docs/superpowers/plans/2026-09-02-practice-request-online-types.md`
- Objetivo: alumnos de máster online (lote con `ONL`, salvo `MONLHC`/`MONLPRS`) solo ven/eligen convalidación experiencia, convalidación TFM y prácticas asíncronas.
- Base: worktree `irg-practice-modality-elearning`, rama `feat/irg-practice-modality-elearning`.

## Knowledge

- `modding_rules_and_email_analysis.md`: addon nuevo `addons-extra/extrairg/`, prefijo `irg_`, herencia.
- `irg_practice_modality_elearning.md`: `practice.request.course_id` es `op.student.course`.
- Detección ONL existente (`'MONL' not in code`) es **incorrecta** para Neurologopedia online (`MONLONL`).

## Clasificación

- **Tier:** `standard` — lógica acotada, un módulo, portal + constraint.
- **Misión:** `full` (comportamiento de producto + control server-side).
- Capacidad: razonamiento alto de esta sesión. Sin selector de modelo.

## Roles

Plan (orquestador) → Implementación/TDD (codificador) → Review (distinto) → Validación → Documentación → Publicación solo con OK.

## E2E

Disparo **sí**: inherit QWeb portal. Check `e2e_testsprite` tras el resto en verde. `projectPath` = `addons-extra/extrairg/irg_practice_request_online_types`.

## Seguridad

Acción protegida (qué tipo puede pedir un alumno). UI no basta.

`[YES] Reason: portal create/write rejects disallowed practice types server-side; sudo keeps portal uid; no secrets, migrations or historical deletes.`

## Criterios de aceptación

- `MONLONL…` online; `MONLHC…` y `MONLPRS…` no; `…ONL…` en otros másteres sí; lote vacío no filtra.
- Portal: combo reducido + POST rechazado si el tipo no aplica.
- Staff backend puede seguir eligiendo cualquier tipo.
- Cero cambios en módulos preexistentes.

## Restricciones

- No commit/push/PR sin OK explícito nuevo.
- Overlay compose `run --rm --no-deps`; no dejar el servicio compartido montado al worktree.
