# Execution — irg-practice-agreement-specific

## Entorno

- Rama: `Dev_iRG`
- Runtime: `docker-compose.local.yml`
- Base: `test_irg_practice_agreement_specific` (clon de `test_irg_practice_agreement_types`)

## Registro

- Spec y plan creados.
- RED: esqueleto sin wizard/campos/QWeb. 3 failed + 7 error(s) of 11 tests
  (el marco con una sola firma ya pasaba). Evidencia: `artifacts/red-tests.txt`.
- GREEN: módulo `irg_practice_agreement_specific` con wizard en la solicitud,
  snapshots, doble firma, plantilla internacional genérica y portal alumno.
  `0 failed, 0 error(s) of 11 tests`. Evidencia: `artifacts/green-tests.txt`.
- Review ronda 1: [NO] — `especifico_nacional` seleccionable y QWeb lo
  trataba como marco. Corregido: valor retirado de la selección + test
  `assertNotIn`; botón de solicitud con `groups` del wizard.
- Review ronda 2: [YES]. `missions/irg-practice-agreement-specific/02b-review.md`.
- Validación independiente: syntax, 11 tests Odoo, git de módulos base
  limpio. E2E TestSprite skipped (MCP ausente). `verification.json` passed.
- Documentación: README del módulo, `doc/modules/extrairg/`, knowledge
  `irg_selection_qweb_predicate_alignment.md`, changelog de misión.
