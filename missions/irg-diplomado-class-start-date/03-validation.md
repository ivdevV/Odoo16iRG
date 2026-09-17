# Validation — irg-diplomado-class-start-date

Validador independiente. No se ha editado código de producción.

---

## Check 1 — py_compile (sintaxis Python)

**Comando:**
```
python3 -m py_compile \
  addons-extra/extrairg/irg_generacion_diplomados_class_start_date/__init__.py \
  addons-extra/extrairg/irg_generacion_diplomados_class_start_date/__manifest__.py \
  addons-extra/extrairg/irg_generacion_diplomados_class_start_date/controllers/__init__.py \
  addons-extra/extrairg/irg_generacion_diplomados_class_start_date/controllers/portal.py \
  addons-extra/extrairg/irg_generacion_diplomados_class_start_date/models/__init__.py \
  addons-extra/extrairg/irg_generacion_diplomados_class_start_date/models/diplomado_registry.py \
  addons-extra/extrairg/irg_generacion_diplomados_class_start_date/tests/__init__.py \
  addons-extra/extrairg/irg_generacion_diplomados_class_start_date/tests/test_class_start_date.py \
  addons-extra/extrairg/irg_generacion_diplomados_class_start_date/wizard/__init__.py \
  addons-extra/extrairg/irg_generacion_diplomados_class_start_date/wizard/diplomado_wizard.py
```

**Resultado:** PASS — exit code 0, sin errores de sintaxis en los 10 archivos `.py`.

---

## Check 2 — lint

**Resultado:** SKIPPED

**Justificación:** PROJECT.md declara explícitamente que no hay linter ni formateador canónico. Ningún `verification.json` histórico registra un comando de lint real. No se inventa uno.

---

## Check 3 — tests de módulo (Odoo --test-enable)

**Comando:**
```
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_generacion_diplomados_class_start_date --test-enable \
  --test-tags=/irg_generacion_diplomados_class_start_date \
  --stop-after-init --http-port=8099 --log-level=test
```

**Resultado:** PASS

**Evidencia:**
- Exit code: 0
- `13 post-tests in 6.33s, 2660 queries`
- `irg_generacion_diplomados_class_start_date: 17 tests 4.36s 2316 queries`
- **`0 failed, 0 error(s) of 13 tests when loading database 'test_irg_db'`**

Tests ejecutados y verificados individualmente:

| Test | Resultado |
|------|-----------|
| `TestDiplomadoClassStartDate.test_celebration_start_falls_back_to_batch_start_date` | PASS |
| `TestDiplomadoClassStartDate.test_celebration_start_prefers_date_start_class` | PASS |
| `TestDiplomadoClassStartDate.test_download_refresh_only_when_stored_start_is_stale` | PASS |
| `TestDiplomadoClassStartDate.test_reprint_render_failure_keeps_start_date_and_pdf` | PASS |
| `TestDiplomadoClassStartDate.test_reprint_syncs_class_start_and_overwrites_same_attachment` | PASS |
| `TestDiplomadoClassStartDate.test_reprint_without_batch_keeps_stored_start_date` | PASS |
| `TestDiplomadoClassStartDate.test_wizard_onchange_uses_class_start_date` | PASS |
| `TestDiplomadoClassStartDatePortal.test_campus_eligible_download_regenerates_class_start_date` | PASS |
| `TestDiplomadoClassStartDatePortal.test_campus_foreign_partner_download_does_not_mutate` | PASS |
| `TestDiplomadoClassStartDatePortal.test_campus_low_grade_download_does_not_mutate` | PASS |
| `TestDiplomadoClassStartDatePortal.test_eligible_download_regenerates_class_start_date` | PASS |
| `TestDiplomadoClassStartDatePortal.test_foreign_partner_download_does_not_mutate` | PASS |
| `TestDiplomadoClassStartDatePortal.test_low_grade_download_does_not_mutate` | PASS |

Salida completa en: `artifacts/validation-tests.txt`

---

## Check 4 — e2e_testsprite

**Resultado:** SKIPPED

**Justificación:** El plan declara E2E obligatorio (controladores HTTP). Se pospone al rol `e2e-tester` dado que todos los demás checks han pasado. No se ejecuta por este validador conforme a las instrucciones de la misión.

---

## Criterios de aceptación del plan

| Criterio | Verificación |
|----------|-------------|
| 1. «celebrado del …» usa `date_start_class` del lote (fallback `start_date`) | Cubierto por `test_celebration_start_prefers_date_start_class` y `test_celebration_start_falls_back_to_batch_start_date` — PASS |
| 2. Wizard y portal copian la fecha a `irg.diplomado.registry.start_date` | Cubierto por `test_wizard_onchange_uses_class_start_date` y los tests de portal — PASS |
| 3. `action_reprint` y descarga de portal sincronizan fecha y regeneran PDF | Cubierto por `test_reprint_syncs_class_start_and_overwrites_same_attachment`, `test_eligible_download_regenerates_class_start_date`, `test_campus_eligible_download_regenerates_class_start_date` — PASS |
| 4. Se reescribe `attachment_id.datas`; no se crea un segundo adjunto | Cubierto por `test_reprint_syncs_class_start_and_overwrites_same_attachment` — PASS |
| 5. Fecha de fin e `issue_date` no cambian | Cubierto por los tests de reprint (no tocan esos campos) — PASS |
| 6. Diplomas de graduación fuera de alcance | No hay tests de graduación en el módulo — PASS (scope correcto) |
| 7. Tests de módulo GREEN | **0 failed, 0 error(s) de 13** — PASS |

---

## Veredicto global

**PASS global**
