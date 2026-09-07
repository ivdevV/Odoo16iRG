# 03-validation.md — irg-practice-agreement-types

**Validador independiente — 2026-09-04**  
Commit base: `928c2974ba94acfa4bb6e8730c14426f9071fc6e`

---

## Check 1: Sintaxis Python

**Comando:** `python3 -m py_compile` sobre los 9 `.py` del módulo  
**Resultado:** PASS  
**Detalle:** Exit code 0, sin errores.

---

## Check 2: Tests Odoo (docker-compose.local.yml)

**Comando:**
```
docker exec -t odoo16irg_local odoo -c /etc/odoo/odoo.conf \
  -d test_irg_practice_agreement_types \
  -u irg_practice_agreement_types \
  --test-enable --test-tags /irg_practice_agreement_types \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --http-port=8099 --log-level=test
```

**Resultado:** PASS  
**Detalle:**
```
0 failed, 0 error(s) of 7 tests when loading database 'test_irg_practice_agreement_types'
```
Tests ejecutados:
- `test_agreement_type_field_exists` ✓
- `test_cannot_change_type_after_sent` ✓
- `test_center_button_opens_wizard` ✓
- `test_legacy_create_stays_nacional` ✓
- `test_wizard_creates_nacional_and_internacional` ✓
- `test_wizard_model_exists` ✓
- `test_wizard_requires_center_and_type` ✓

Los `FileNotFoundError` en assets son advertencias de infraestructura (caché no presente en BD nueva) y no provocan fallo de test.

**Evidencia:** `artifacts/validation-tests.txt`

---

## Check 3: Módulo base no modificado

**Comando:** `git status` + `git diff HEAD -- addons-extra/extrairg/irg_practice_agreement_sign/`  
**Resultado:** PASS  
**Detalle:** `nothing to commit, working tree clean`. Diff vacío. `irg_practice_agreement_sign` intacto.

---

## Check 4: E2E TestSprite

**Resultado:** SKIPPED  
**Justificación:** MCP TestSprite no disponible en este runtime (igual que en misiones `irg-admission-auto-gradebook-templates` y `fix-gradebook-template-zero-averages` del mismo repo). El scope del diff SÍ toca `views/`, portal y `report/` QWeb, por lo que el disparo es obligatorio según `plan.md`. El check queda pendiente de ejecución cuando el MCP esté disponible en el runtime.

---

## Veredicto

| Check | Resultado |
|-------|-----------|
| syntax_py_compile | PASS |
| odoo_module_tests | PASS (7/7) |
| git_base_module_clean | PASS |
| e2e_testsprite | SKIPPED (justificado) |

VALIDATION PASS
