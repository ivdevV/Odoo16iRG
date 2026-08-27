# irg-business-api

## 16.0.1.0.0 — 2026-08-27

Addon nuevo `irg_business_api`: fachada `irg.api.operation` para lecturas académicas paginadas y escrituras eLearning en borrador (fases 0–2).

- Entrada: `create` con código allowlist, JSON y `idempotency_key`. Lecturas quedan `verified`; escrituras quedan en `preview` hasta `action_approve`.
- `write()` y `unlink()` siempre `AccessError`. Mutación interna con `super().write()`, sin flags de contexto RPC.
- Grupo `group_irg_business_api_user`, record rules por propietario/compañía, denylist de secretos, entornos `test`/`beta`.
- Borradores de slide: artículo no publicado. Publicar y despublicar son operaciones distintas.
- Fuera de alcance: clonación, matrícula, Moodle de escritura, encuestas de escritura, HTTP público, Lisa MCP config.

Pruebas Odoo: 38 tests, 0 fallos (`--test-tags /irg_business_api`). E2E TestSprite no se ejecutó (MCP ausente en el runtime).
