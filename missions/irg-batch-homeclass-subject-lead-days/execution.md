# Execution: irg-batch-homeclass-subject-lead-days

- 2026-09-18: misión `full`, tier `standard`. Spec y plan escritos. E2E skipped
  por scope (sin superficie web). Security Advisor no aplica. Sin autorización
  de commit, push ni PR.
- 2026-09-18: rama `feat/irg-batch-homeclass-subject-lead-days` desde `Dev_iRG`.
  Trabajo en el checkout principal porque `docker-compose.local.yml` monta
  `addons-extra` desde ahí.
- 2026-09-18: RED. Fixture de `op.course` necesita `lang`. Tras el arreglo,
  3 failed / 0 errors: `date_from` 16/01 != 13/01. Evidencia
  `artifacts/red-tests.txt`.
- 2026-09-18: GREEN. Offset de 3 días en `_irg_apply_homeclass_subject_lead_days`.
  0 failed, 0 error(s) of 5 tests en BD `test_irg_hc_lead`. Evidencia
  `artifacts/green-tests.txt`.
- 2026-09-18: Review independiente [Review](1d14d73a-57c7-4f6f-91e4-0634066993ba)
  `REVIEW OK` (0 BLOQUEANTE, 0 MENOR, 2 NIT). `02b-review.md`.
- 2026-09-18: Validación independiente [Validate](82800cb6-a9ba-4f3b-924c-3313198dda9c)
  `verification.json` status `passed`. BD desechable dropeada. `odoo16irg_local`
  sigue en el checkout principal.
- 2026-09-18: Documentación: ficha del módulo, changelog, knowledge, índices.
  Sin cambios de código de producción. Sin autorización de commit, push ni PR.


