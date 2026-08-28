# Validación — irg-business-api-phases-3-6

Validador independiente. Re-ejecución 2026-08-28 (no se confió en `artifacts/tdd.txt`).

Base commit: `6b3e932e1e6ad2da31d5ec66fc1361f0c0ce08ba`

## Checks

| Check | Resultado | Evidencia |
| --- | --- | --- |
| `python_compile` | **PASS** | `python3 -m compileall -q addons-extra/extrairg/irg_business_api` → exit 0 |
| `xml_wellformed` | **PASS** | `xmllint --noout` OK en 3 XML existentes; ninguno en el diff |
| `odoo_tests` | **PASS** | 0 failed, 0 error(s) of 53 tests; 65 tests irg_business_api en 0.81s |
| `e2e_testsprite` | **skipped** | Diff solo Python (models/tests); plan declara skip sin vistas/static/HTTP |
| `cleanup` | **PASS** | `DROP DATABASE test_irg_business_api`; overlay monta worktree en `/mnt/extra-addons` |

## Detalle por criterio de aceptación (plan)

- Clonación Online (`test_online_clone_operations`): ejecutado en suite Odoo — PASS (0 failures).
- Aperturas/accesos y guardarraíl 30 % (`test_later_phase_operations`, `test_access_permissions`): ejecutados — PASS.
- Matrícula rechaza admisión `done` (`test_apply_enrollment_refuses_already_done`): ejecutado — PASS.
- Tests `/irg_business_api` en verde: **PASS** (53 post-tests, 0 failed).

## Montaje worktree

Overlay `missions/irg-business-api/docker-compose.worktree.yml`:

```
source: .../.worktrees/irg-business-api/addons-extra
target: /mnt/extra-addons (ro)
```

`survey_service.py` visible en contenedor; no apunta al checkout principal.

## Veredicto

**PASS global**
