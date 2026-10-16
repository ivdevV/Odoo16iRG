# Execution — irg-admission-unimarconi-mail

## 2026-10-15 — Plan

- Jev intake al inicio de la petición: `skipped` / `http_error`. Clasificación
  del orquestador: `full`, tier `complex`. Security Advisor no aplica.
- Diseño aprobado por el usuario:
  `docs/superpowers/specs/2026-10-15-irg-admission-unimarconi-mail-design.md`.
- Plan de implementación:
  `docs/superpowers/plans/2026-10-15-irg-admission-unimarconi-mail.md`.
- Implementación no empezada.

## 2026-10-15 — Implementación

- Modo: subagentes en el checkout principal (`Dev_iRG` @ `2e3da613d`). Sin
  commit. Sin worktree: `docker-compose.local.yml` monta `addons-extra`.
- Task 1: helper `startswith('MO')` y campo calculado. Fixture de curso con
  `lang` y tests `post_install` porque `op.course.lang` es NOT NULL y no
  existe en at-install. Review SPEC OK / QUALITY OK.
- Task 2: plantilla y logo. El nombre del curso va en `<t t-out>` dentro de
  `<strong>Para tu …</strong>` para que la frase quede continua. Review OK.
- Task 3: acción del compositor y botón. `op.admission.email` es related de
  `partner_id.email` (`isep_openeducat_sale`); el test de correo vacío anula
  el email del partner. Review OK.
- Task 4: README. Árbol de 10 archivos. Diff de oficialidad vacío. Review OK.
- Review final del módulo: APPROVED.
- Validación independiente: `-u` en `test_irg_unimarconi_mail`,
  `0 failed, 0 error(s) of 14 tests`. Evidencia:
  `artifacts/validation-tests.txt`.

## 2026-10-16 — E2E

- TestSprite, dos corridas, las dos BLOCKED: primero pantalla en blanco y
  después login rechazado. En servidor, la admisión MO mostraba el botón y
  la MP no.
- Limpieza: contenedor `e2e_odoo_unimarconi` eliminado, base
  `e2e_unimarconi_20261015` borrada, `odoo16irg_local` vuelto a levantar
  (`/web/health` 200).
- `verification.json` queda en `failed` por el gate E2E. Sin commit.
