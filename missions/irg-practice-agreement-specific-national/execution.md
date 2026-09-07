# Execution — irg-practice-agreement-specific-national

## Entorno

- Rama: `Dev_iRG`
- Runtime: `docker-compose.local.yml`
- Base: `test_irg_practice_agreement_specific`
- **Excepción:** se edita `irg_practice_agreement_specific` (autorizada
  por el usuario; no se crea un módulo nuevo solo para la variante
  nacional). No se tocan `irg_practice_agreement_sign` ni
  `irg_practice_agreement_types`.

## Registro

- Spec y plan creados. TDD a continuación.
- RED: 1 failed, 3 error(s) of 15 tests (`artifacts/red-tests.txt`).
  El tipo `especifico_nacional` no existía en selection/wizard/QWeb.
- Implementación mínima en el módulo existente: `selection_add`, radio
  del wizard, QWeb nacional, predicados Python/QWeb alineados, filename
  `Convenio_Especifico_Nacional_...`.
- GREEN: `0 failed, 0 error(s) of 15 tests`
  (`artifacts/green-tests.txt`).
- Review independiente: `REVIEW OK` (0 bloqueantes). `02b-review.md`.
- Validación independiente: `VALIDATION PASS`. `verification.json`
  `passed`. E2E TestSprite `skipped` (MCP ausente; no por alcance).
- Documentación: README del módulo, `doc/modules/extrairg/`, CHANGELOG,
  knowledge de la excepción (mismo módulo) y corrección del patrón
  Selection/QWeb. Sin cambios de código en esta fase.
