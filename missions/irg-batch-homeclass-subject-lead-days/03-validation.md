# Validación — irg-batch-homeclass-subject-lead-days

Validador independiente. Sin edición de código de producción. Review previa: REVIEW OK.
Runtime: `docker-compose.local.yml`. Base: `test_irg_hc_lead`.
HEAD: `35c912bc7c2d2c7564a7e7a9f39e82fb79f558b4`. Capacidad: `standard`.

## Checks

| Check | Resultado | Detalle |
| --- | --- | --- |
| `syntax_py_compile` | **PASS** | 6 `.py` compilados, exit 0. `artifacts/py-compile.txt` |
| `lint` | **SKIPPED** | No hay linter canónico en el proyecto. `artifacts/lint.txt` |
| `odoo_module_tests` | **PASS** | Re-ejecución independiente: `0 failed, 0 error(s) of 5 tests`. `artifacts/validation-tests.txt` |
| `scheduler_unmodified` | **PASS** | `git status --short` vacío sobre `irg_batch_homeclass_api_scheduler`. |
| `e2e_testsprite` | **SKIPPED** | Diff sin vistas/QWeb/`static`/portal/website/HTTP/diplomas. `artifacts/e2e-testsprite.txt` |
| `cleanup` | **PASS** | 0 conexiones; `DROP DATABASE test_irg_hc_lead`; `odoo16irg_local` Up montando el checkout principal. `artifacts/cleanup.txt` |

## Gate

`verification.json`: `status: passed`.

PASS global
