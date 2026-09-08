# Execution log — irg-practice-request-online-types

- 2026-09-02: misión abierta. Filtro de tipos de práctica para másteres online según código de lote.
- Detección: `ONL` en `batch.code`, exceptuando prefijos `MONLHC` y `MONLPRS`.
- Tipos permitidos: `validation`, `tfm_validation`, `homeclass_asincronas`.
- No se usa `'MONL' not in code` porque `MONLONL` es la variante online de Neurologopedia.
- TDD: RED fixture `lang` en `op.course` (deps mínimas). GREEN: `0 failed, 0 error(s) of 8 tests` en `test_irg_ot_20260902`. Overlay `run --rm --no-deps`. Evidencia: `artifacts/green-tests.txt`.
- Review 1: REVIEW FAIL (JS desocultaba la opción legacy id=2; reasignación sin `change`). Corregido. Review 2: REVIEW OK.
- Validación independiente: `verification.json` `passed`. E2E skipped (sin TestSprite MCP).
- Documentación: `doc/modules/extrairg/irg_practice_request_online_types.md`, knowledge `irg_practice_request_online_types.md`.
- Sin commit, push ni PR.
