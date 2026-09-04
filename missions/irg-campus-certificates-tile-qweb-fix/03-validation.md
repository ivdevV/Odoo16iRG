# Validation Report: irg-campus-certificates-tile-qweb-fix

**Fecha:** 2026-09-04  
**Validador:** agente independiente (rol: validator)  
**Runtime:** docker-compose.local.yml · DB: test_irg_db  
**Base commit:** 52c3e5d83

---

## Checks

### 1. py_compile — PASS

**Comando:**
```
python3 -m py_compile \
  addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/__init__.py \
  addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/__manifest__.py \
  addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/tests/__init__.py \
  addons-extra/extrairg/irg_campus_certificates_tile_qweb_fix/tests/test_qweb_guard.py
```

**Resultado:** exit code 0 — sin errores de sintaxis en ninguno de los 4 archivos .py.

---

### 2. xml_parse — PASS

**Comando:**
```
python3 -c "import xml.etree.ElementTree as ET; ET.parse('...campus_dashboard_override.xml'); print('xml_parse: OK')"
```

**Resultado:** `xml_parse: OK` — el XML es válido.

**Contenido relevante del nodo t-if (confirmación spec 1 y 2):**
```xml
<attribute name="t-if">not course_id.is_diplomado()</attribute>
```
- ✅ No contiene `hasattr`
- ✅ Usa `course_id.is_diplomado()`

---

### 3. lint — SKIPPED

**Justificación:** No existe linter canónico definido en PROJECT.md ni en la knowledge base del proyecto. El check no aplica al scope de este módulo.

---

### 4. module_tests — PASS

**Comando:**
```
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_campus_certificates_tile_qweb_fix --test-enable \
  --test-tags=/irg_campus_certificates_tile_qweb_fix \
  --stop-after-init --http-port=8099 --log-level=test
```

**Resultado (extracto relevante del log):**
```
INFO  Loading module irg_campus_certificates_tile_qweb_fix (242/245)
INFO  loading irg_campus_certificates_tile_qweb_fix/views/campus_dashboard_override.xml
INFO  Module irg_campus_certificates_tile_qweb_fix loaded in 0.30s, 44 queries
INFO  Starting TestCertificatesTileQwebGuard.test_combined_t_if_does_not_use_hasattr ...
INFO  Starting TestCertificatesTileQwebGuard.test_diplomado_tile_guard_hides_tile ...
INFO  Starting TestCertificatesTileQwebGuard.test_master_tile_guard_renders_without_typeerror ...
INFO  3 post-tests in 0.12s, 74 queries
INFO  0 failed, 0 error(s) of 3 tests when loading database 'test_irg_db'
```

**Evidencia completa:** `artifacts/validation-tests.txt`

Tests ejecutados y resultado:

| Test | Spec cubierta | Resultado |
|---|---|---|
| `test_combined_t_if_does_not_use_hasattr` | Spec 1 + 2: sin hasattr, usa is_diplomado() | ✅ PASS |
| `test_diplomado_tile_guard_hides_tile` | Spec 4: diplomado (DI…) oculta el tile | ✅ PASS |
| `test_master_tile_guard_renders_without_typeerror` | Spec 3 + 4: sin TypeError, máster muestra tile | ✅ PASS |

---

### 5. portal_no_edit — PASS

**Comando:**
```
git status addons-extra/extrairg/irg_campus_certificates_portal/
```

**Resultado:** `nothing to commit, working tree clean`  
El módulo `irg_campus_certificates_portal` no fue modificado. ✅ Spec 5 cumplida.

---

### 6. manifest_checks — PASS

**auto_install:** `True` ✅  
**depends incluye `irg_course_portal_tiles_diplomado_hide`:** ✅  
**depends incluye `irg_campus_certificates_portal`:** ✅

---

### 7. e2e_testsprite — PENDIENTE

El validador no ejecuta TestSprite. El diff toca una vista QWeb de portal (`views/campus_dashboard_override.xml`), por lo que según AGENTS.md la capa E2E es **obligatoria**. El orquestador lanzará el rol `e2e-tester` a continuación. Este check no cierra la misión hasta que `e2e-tester` emita `E2E PASS`.

---

## Resumen de spec

| Criterio | Verificación | Estado |
|---|---|---|
| 1. t-if sin hasattr | XML inspeccionado + test 1 | ✅ |
| 2. Usa course_id.is_diplomado() | XML inspeccionado + test 1 | ✅ |
| 3. Sin TypeError al renderizar | test_master_tile_guard_renders_without_typeerror | ✅ |
| 4. Máster muestra / DI… oculta | test_master + test_diplomado | ✅ |
| 5. irg_campus_certificates_portal no editado | git status clean | ✅ |

---

VALIDATION PASS
