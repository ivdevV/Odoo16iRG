# Validation — irg-admission-auto-gradebook-templates

Fecha: 2026-07-21  
Validador: independiente del codificador (validator subagent)

---

## Task 1 — Scaffold module + failing tests

### Check 1: Sintaxis Python

**Comando:**
```bash
python3 -m py_compile \
  addons-extra/extrairg/irg_admission_auto_gradebook_templates/__init__.py \
  addons-extra/extrairg/irg_admission_auto_gradebook_templates/__manifest__.py \
  addons-extra/extrairg/irg_admission_auto_gradebook_templates/models/__init__.py \
  addons-extra/extrairg/irg_admission_auto_gradebook_templates/models/op_admission.py \
  addons-extra/extrairg/irg_admission_auto_gradebook_templates/tests/__init__.py \
  addons-extra/extrairg/irg_admission_auto_gradebook_templates/tests/test_auto_gradebook_templates.py
```

**Resultado:** `PASS` — exit code 0, todos los archivos compilan sin error.

---

## Task 2 — Data + enrollment override

### Check 2: Suite Odoo completa (6 tests)

**Comando:**
```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf \
  -d test_irg_agtpl_20260721_val \
  -i irg_admission_auto_gradebook_templates \
  --test-enable --test-tags=/irg_admission_auto_gradebook_templates \
  --stop-after-init --http-port=8099 --log-level=test
```

**Resultado:** `PASS`

Evidencia clave (extracto de `artifacts/validation-tests.txt`):

```
INFO odoo.tests.stats: irg_admission_auto_gradebook_templates: 8 tests 0.35s 626 queries
INFO odoo.tests.result: 0 failed, 0 error(s) of 6 tests when loading database 'test_irg_agtpl_20260721_val'
```

Tests individuales confirmados vía INFO del módulo:
- `test_course_with_template_gets_assigned` — PASS (plantilla de curso asignada)
- `test_diplomado_by_course_type_gets_diplomado_template` — PASS (canon diplomado)
- `test_master_by_course_name_gets_solo_examen` — PASS (canon máster por nombre)
- `test_master_by_course_type_gets_solo_examen` — PASS (canon máster por tipo)
- `test_other_course_without_template_stays_empty` — PASS (sin plantilla → vacío)
- `test_subject_lines_not_force_written` — PASS (líneas de asignatura no sobreescritas)

Notas: Los `ERROR odoo.schema: unable to set NOT NULL` son advertencias de migración no fatales en la DB de test (columnas preexistentes con NULL). No afectan los tests del módulo.

---

## Task 3 — Artefactos de misión

- `plan.md` existente ✓
- `execution.md` existente ✓
- `artifacts/validation-tests.txt` generado ✓
- `verification.json` emitido con `status: passed` ✓

---

## PASS global

Todos los checks pasan. 0 fallos, 0 errores en la suite de 6 tests. Sintaxis Python OK en todos los archivos del módulo.
