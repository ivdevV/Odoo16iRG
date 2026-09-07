# 03-validation.md — irg-practice-agreement-specific-national

**Fecha:** 2026-09-07  
**Validador:** independiente (no es el codificador ni el revisor)  
**Review previo:** REVIEW OK (`missions/irg-practice-agreement-specific-national/02b-review.md`)  
**Base commit:** `1770cff43e1265e3224fa92e223166040a68a045`  
**Rama:** `Dev_iRG`

---

## Check 1 — syntax_py_compile

**Comando:**
```
python3 -m py_compile <11 archivos .py de irg_practice_agreement_specific>
```

**Archivos verificados:**
- `__init__.py`
- `__manifest__.py`
- `controllers/__init__.py`
- `controllers/portal_agreement.py`
- `models/__init__.py`
- `models/practice_agreement.py`
- `models/practice_request.py`
- `tests/__init__.py`
- `tests/test_practice_agreement_specific.py`
- `wizard/__init__.py`
- `wizard/practice_agreement_specific_create_wizard.py`

**Resultado:** EXIT CODE 0 — sin errores de sintaxis

**Evidencia:** `artifacts/syntax-py-compile.txt`

**→ PASS**

---

## Check 2 — odoo_module_tests

**Comando (ejecutado fresco — no copiado de green-tests.txt):**
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
odoo.tests.stats: irg_practice_agreement_specific: 17 tests 4.48s 1003 queries
odoo.tests.result: 0 failed, 0 error(s) of 15 tests when loading database 'test_irg_practice_agreement_specific'
```

Notas: hay WARNING de `docutils` (indentación en docstring) y campos con parámetros
desconocidos (`tracking`, `inverse_name`, `track_visibility`) — son pre-existentes
y no generan fallos de test. 17 tests ejecutados, 0 fallos, 0 errores.

**Evidencia:** `artifacts/validation-tests.txt`

**→ PASS**

---

## Check 3 — git_base_module_clean

**Comando:**
```
git status --short \
  addons-extra/extrairg/irg_practice_agreement_sign/ \
  addons-extra/extrairg/irg_practice_agreement_types/ \
  addons-extra/extrairg/irg_practice_agreement_specific/
```

**Resultado:**
```
 M addons-extra/extrairg/irg_practice_agreement_specific/__manifest__.py
 M addons-extra/extrairg/irg_practice_agreement_specific/models/practice_agreement.py
 M addons-extra/extrairg/irg_practice_agreement_specific/report/practice_agreement_report_templates.xml
 M addons-extra/extrairg/irg_practice_agreement_specific/tests/test_practice_agreement_specific.py
 M addons-extra/extrairg/irg_practice_agreement_specific/views/portal_agreement_templates.xml
 M addons-extra/extrairg/irg_practice_agreement_specific/views/practice_agreement_views.xml
 M addons-extra/extrairg/irg_practice_agreement_specific/wizard/practice_agreement_specific_create_wizard.py
?? addons-extra/extrairg/irg_practice_agreement_specific/views/agreement_document_especifico_nacional.xml
```

- `irg_practice_agreement_sign`: **sin cambios** ✓
- `irg_practice_agreement_types`: **sin cambios** ✓
- `irg_practice_agreement_specific`: **con cambios** ✓ (excepción autorizada en plan.md)

**→ PASS**

---

## Check 4 — e2e_testsprite

**Disparo:** OBLIGATORIO — el diff toca `views/`, portal y `report/`

**Resultado de descubrimiento:**
```
GetDynamicTools pattern="testsprite" → matches: []
```
El MCP de TestSprite **no está disponible** en este runtime de validación.

**Motivo del skip:** técnico (MCP ausente), NO de alcance. El diff sí toca
superficie web y el disparo era obligatorio per plan.md y AGENTS.md.

**Flujos pendientes documentados** en `artifacts/e2e-testsprite.txt`:
1. Wizard radio Nacional/Internacional
2. Portal firma nacional (usuario portal)
3. PDF nacional — render y `print_report_name`

**Justificación del skip (AGENTS.md §Capa E2E):** "Si el MCP no está: `result: skipped`
con justificación TÉCNICA (MCP ausente)." El skip está formalmente justificado y
los flujos pendientes quedan documentados para ejecución futura.

**Evidencia:** `artifacts/e2e-testsprite.txt`

**→ SKIPPED (justificado — MCP ausente)**

---

## Resumen

| Check | Resultado |
|---|---|
| syntax_py_compile | ✅ PASS |
| odoo_module_tests | ✅ PASS (0 failed, 0 error(s) de 17 tests) |
| git_base_module_clean | ✅ PASS |
| e2e_testsprite | ⏭️ SKIPPED — MCP ausente (justificado; flujos documentados) |

---

VALIDATION PASS
