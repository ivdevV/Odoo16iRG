# Ejecución — irg-business-api

## 2026-08-27 — Plan

- Se leyó el plan técnico, la ejecución de preparación de Lisa y su verification (addon aún inexistente).
- Knowledge: modding rules, auto-enroll robusto, routing Moodle, `AGENTS.md`, `SPECIFICATIONS.md`.
- Worktree: `/Users/ivrogo/Workspace/Proyectos iRG/Odoo16iRG/.worktrees/irg-business-api`
- Rama: `feat/irg-business-api` desde `Dev_iRG` (`41628848d`).
- Misión completa, tier `complex`. Security Advisor obligatorio. E2E obligatorio por `views/`.
- Publicación: el usuario autorizó merge local a la rama de desarrollo; no se infiere push.

## Registro de fases

### Plan

- Micro-spec, design y plan de misión creados antes del código de producción.
- Overlay Docker: `missions/irg-business-api/docker-compose.worktree.yml` (local; `docker-compose.*.yml` está en `.gitignore`).
- Security Advisor: `[YES]` en `artifacts/security-advisor.txt`.

### Implementación / TDD

- RED inicial: el addon no existía; primer fallo de runtime `self.env.sudo()` → `AttributeError`. Corregido a `self.sudo().env`.
- Serializer: `date`/`datetime`/`Markup` a JSON. Cache: `invalidate_recordset`.
- Concurrencia: `write_date` a segundo era demasiado grueso; preview/apply compara campos de negocio.
- GREEN: 37 tests, luego 38 tras el fix de review (`artifacts/tdd-green.txt`).
- Review bloqueó `write()` que confiaba en `context['irg_api_internal']`. Fix: `write()` siempre `AccessError`; `_irg_internal_write` usa `super().write()`; apply con allowlist y `SELECT FOR UPDATE`.

### Review de código

- Primera pasada: BLOCK (`artifacts/review.txt`).
- Re-review independiente: APPROVE. Notas menores no bloqueantes (paginación de recordset, `irg_section_id` con `int()`, preview de slide publicado).

### Validación

Independiente, sin editar código de producción. `verification.json` status `passed`.

- `python_compile` pass
- `xml_wellformed` pass
- `module_install` pass
- `odoo_tests` pass (38 tests, 0 failed)
- `e2e_testsprite` skipped: TestSprite MCP ausente en este runtime de Cursor (justificado; no se registra como pass)
- `cleanup` pass: `test_irg_business_api` eliminada; `odoo_local` persistente sigue montando el checkout principal

### Documentación

- README y contrato del addon, ficha `doc/modules/extrairg/irg_business_api.md`, índice extrairg, CHANGELOG de misión.
- Knowledge reutilizable: `.agents/knowledge/odoo_development_modding/artifacts/irg_business_api_command_facade.md`.

### Publicación

- Commit en `feat/irg-business-api` y merge local a `Dev_iRG`. Sin push.
