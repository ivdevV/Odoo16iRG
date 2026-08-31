# Validación — irg_diplomado_fixed_issue_date

Fecha: 2026-08-31  
Validador: agente independiente (no editó código de producción)  
Base commit: `128fb02e19ca6a6c1b32ab3e1f88dae48750e5d8`

---

## Check 1: Sintaxis Python (`compileall`)

**Comando:**
```
python3 -m compileall -q addons-extra/extrairg/irg_generacion_diplomados_fixed_issue_date
```

**Resultado: PASS**  
Exit code 0. Sin errores de compilación en ningún archivo del módulo.

---

## Check 2: Tests unitarios Odoo

**Comando:**
```
docker compose -f docker-compose.local.yml \
  -f missions/irg_diplomado_fixed_issue_date/docker-compose.worktree.yml \
  run --rm --no-deps -T odoo_local \
  odoo -c /etc/odoo/odoo.conf \
  -d test_irg_dip_issue_date_val \
  -i irg_generacion_diplomados_fixed_issue_date \
  --test-enable \
  --test-tags /irg_generacion_diplomados_fixed_issue_date \
  --stop-after-init --http-port=8099 --log-level=test
```

Base desechable: `test_irg_dip_issue_date_val` clonada de `test_irg_db`. Eliminada al terminar (DROP ejecutado con éxito).

**Resultado: PASS — 6 tests, 0 failed, 0 errors**

Línea de resultado del log:
```
0 failed, 0 error(s) of 6 tests when loading database 'test_irg_dip_issue_date_val'
```

Tests individuales ejecutados (todos PASS):
| Test | Resultado |
|---|---|
| `test_helper_returns_september_26_of_generation_year` | PASS |
| `test_print_stores_fixed_issue_date_on_registry` | PASS |
| `test_registry_default_is_september_26_of_generation_year` | PASS |
| `test_registry_keeps_explicit_issue_date` | PASS |
| `test_wizard_create_forces_september_26_ignoring_other_date` | PASS |
| `test_wizard_write_cannot_keep_another_date` | PASS |

Evidencia completa: `artifacts/odoo-tests-raw.txt`  
Resumen: `artifacts/green-tests.txt`

---

## Check 3: E2E TestSprite

**Resultado: SKIPPED**  
Justificación: El diff no toca vistas XML, QWeb (`.xml` bajo `views/`, `templates/` o `report/`), `static/`, portal, `website` ni controladores HTTP. El scope es exclusivamente Python (`models/`, `wizard/`, `tests/`). Declarado en `plan.md`.

---

## Veredicto global

**PASS global**

Todos los criterios de aceptación del plan están cubiertos y verificados con evidencia real:
- Helper `_irg_fixed_issue_date()` devuelve 26/09 del año en curso.
- Wizard fuerza la fecha en `create` y `write`, ignorando valores distintos.
- Registro sin `issue_date` explícita usa 26/09 del año en curso.
- Registro con `issue_date` explícita conserva esa fecha.
- `action_print_diplomado` graba 26/09 en el registro resultante.
- El formato devuelto por `_format_issue_date` es `"26 de Septiembre de {año}"`.
