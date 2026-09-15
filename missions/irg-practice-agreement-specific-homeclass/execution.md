# Execution — irg-practice-agreement-specific-homeclass

## Entorno

- Rama: `Dev_iRG`
- Runtime: `docker-compose.local.yml`
- Base: `test_irg_practice_agreement_specific`
- **Excepción:** se edita `irg_practice_agreement_specific` (misma
  excepción que el nacional). No se tocan `sign` ni `types`.

## Registro

- Spec y plan creados. TDD a continuación.
- RED: 1 failed, 3 error(s) of 18 tests (`artifacts/red-tests.txt`).
- GREEN: `0 failed, 0 error(s) of 18 tests` (`artifacts/green-tests.txt`).
- Review independiente: `REVIEW OK` (0 bloqueantes). `02b-review.md`.
- Validación: `VALIDATION PASS`. `verification.json` `passed`.
  E2E TestSprite `skipped` (MCP ausente; no por alcance).
- Documentación: README, `doc/modules/extrairg/`, CHANGELOG y knowledge
  del mismo módulo. Sin cambios de código en esta fase.
