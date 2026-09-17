# Validación independiente — irg-practice-agreement-specific

Validador: agente independiente (no el codificador).  
Fecha: 2026-09-07  
Commit base: `928c2974ba94acfa4bb6e8730c14426f9071fc6e`  
Review: REVIEW OK (ronda 2) — `02b-review.md`

---

## Check 1 — syntax_py_compile

**Comando:**
```
python3 -m py_compile <11 ficheros .py del módulo>
```

**Resultado:** PASS  
**Evidencia:** `artifacts/syntax-py-compile.txt`

Los 11 ficheros Python del módulo compilan sin errores de sintaxis (exit 0, salida vacía).

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

**Resultado:** PASS  
**Evidencia:** `artifacts/validation-tests.txt`

Tests ejecutados (11):
- `test_agreement_type_includes_especifico_internacional` — OK
- `test_both_signatures_complete` — OK
- `test_center_signature_alone_does_not_complete` — OK
- `test_html_has_insurance_and_no_inmira` — OK
- `test_html_shows_optional_activities` — OK
- `test_marco_still_completes_with_center_only` — OK
- `test_request_button_opens_wizard` — OK
- `test_student_and_center_urls_differ` — OK
- `test_wizard_creates_especifico_with_snapshots` — OK
- `test_wizard_model_exists` — OK
- `test_wizard_requires_assigned_center` — OK

Línea de resultado Odoo:
```
0 failed, 0 error(s) of 11 tests when loading database 'test_irg_practice_agreement_specific'
```

Notas: los avisos de caché de assets (`Failed to find attachment for assets`) y los WARNING de campos de módulos base son esperados en la BD de pruebas y no afectan al resultado.

---

## Check 3 — git_base_module_clean

**Comando:**
```
git status -- addons-extra/extrairg/irg_practice_agreement_sign/
git diff --name-only -- addons-extra/extrairg/irg_practice_agreement_sign/ addons-extra/extrairg/irg_practice_agreement_types/
```

**Resultado:** PASS

- `irg_practice_agreement_sign`: working tree clean, ninguna modificación.
- `irg_practice_agreement_types`: untracked (módulo nuevo independiente, sin modificaciones sobre ningún fichero de origen).
- `git diff --name-only` devuelve vacío para ambos módulos.

El módulo `irg_practice_agreement_specific` es untracked completo (nuevo), sin tocar los módulos base.

---

## Check 4 — e2e_testsprite

**Resultado:** SKIPPED  
**Justificación:** Ejecución diferida al e2e-tester tras checks de módulo. El diff toca views/, portal, report/ y controladores HTTP, por lo que la capa E2E es obligatoria por policy. El check se registra skipped aquí y se completa por el orquestador mediante el subagente `e2e-tester` una vez confirmado que los checks de módulo no fallan.

---

## Veredicto global

**PASS global**

Todos los checks ejecutables pasan. El único skipped (`e2e_testsprite`) tiene justificación no vacía y su ejecución está diferida explícitamente al e2e-tester por instrucción del orquestador.
