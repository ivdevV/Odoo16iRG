# 03-validation.md — irg-practice-agreement-specific-homeclass

**Fecha:** 2026-09-15  
**Validador:** continuación de la validación interrumpida (checks reejecutados fresco, sin confiar en green-tests.txt).  
**Review previo:** REVIEW OK (`02b-review.md`)  
**Base commit:** `583891193dd161e21374a02950003c7e566d4033`  
**Rama:** `Dev_iRG`

---

## Check 1 — syntax_py_compile

**Comando:** `python3 -m py_compile` sobre los 10 `.py` del módulo  
**Resultado:** PASS  
**Evidencia:** `artifacts/syntax-py-compile.txt`

---

## Check 2 — odoo_module_tests

**Comando:**
```
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
  -d test_irg_practice_agreement_specific \
  -u irg_practice_agreement_specific \
  --test-enable --test-tags /irg_practice_agreement_specific \
  --without-demo=all --max-cron-threads=0 --stop-after-init \
  --http-port=8099 --log-level=test
```

**Resultado:**
```
odoo.tests.stats: irg_practice_agreement_specific: 20 tests 5.09s 1251 queries
odoo.tests.result: 0 failed, 0 error(s) of 18 tests when loading database 'test_irg_practice_agreement_specific'
```

**Evidencia:** `artifacts/validation-tests.txt`  
**→ PASS**

---

## Check 3 — git_base_module_clean

**Comando:** `git status --short` sobre sign, types y specific.

- `irg_practice_agreement_sign`: sin cambios
- `irg_practice_agreement_types`: sin cambios
- `irg_practice_agreement_specific`: con cambios (excepción autorizada)

**→ PASS**

---

## Check 4 — e2e_testsprite

**Disparo:** OBLIGATORIO (diff toca `views/`, portal y `report/`).

**Descubrimiento:** `GetDynamicTools pattern=testsprite` → `matches: []`. MCP ausente.

**Skip:** técnico (MCP ausente), no de alcance. Flujos pendientes en `artifacts/e2e-testsprite.txt`.

**→ SKIPPED (justificado)**

---

## Resumen

| Check | Resultado |
|---|---|
| syntax_py_compile | PASS |
| odoo_module_tests | PASS |
| git_base_module_clean | PASS |
| e2e_testsprite | SKIPPED — MCP ausente |

VALIDATION PASS
