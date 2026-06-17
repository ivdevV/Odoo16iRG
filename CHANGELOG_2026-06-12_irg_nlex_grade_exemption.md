# Registro de Cambios - irg_nlex_grade_exemption (2026-06-12)

Este documento contiene el resumen de cambios, pruebas superadas y archivos añadidos durante el desarrollo del módulo `irg_nlex_grade_exemption` para Odoo 16.

---

## Archivos Añadidos

### Código y Vistas del Módulo:
* `addons-extra/extrairg/irg_nlex_grade_exemption/__init__.py`
* `addons-extra/extrairg/irg_nlex_grade_exemption/__manifest__.py`
* `addons-extra/extrairg/irg_nlex_grade_exemption/models/__init__.py`
* `addons-extra/extrairg/irg_nlex_grade_exemption/models/app_gradebook_student.py`
* `addons-extra/extrairg/irg_nlex_grade_exemption/models/ap_gradebook_summary.py`
* `addons-extra/extrairg/irg_nlex_grade_exemption/tests/__init__.py`
* `addons-extra/extrairg/irg_nlex_grade_exemption/tests/test_nlex_grade_exemption.py`
* `addons-extra/extrairg/irg_nlex_grade_exemption/views/certified_diploma.xml`
* `addons-extra/extrairg/irg_nlex_grade_exemption/views/report_gradebook.xml`

### Documentación del Proyecto:
* `doc/modules/extrairg/irg_nlex_grade_exemption.md` (Ficha técnica y manual del módulo)
* `CHANGELOG_2026-06-12_irg_nlex_grade_exemption.md` (Este archivo)

---

## Resumen de Cambios

1. **Estructura base del módulo**:
   * Creación del manifiesto y la configuración inicial con dependencias a `isep_gradebook`, `isep_control_escolar`, `dec_document`, `isep_openeducat_reports` y `l10n_mx_edi_extended`.

2. **Cierre de Libreta sin notas NLEX**:
   * Modificación de la validación del método `state_to_done()` en `app.gradebook.student` para ignorar las materias NLEX sin calificaciones o exámenes cargados.

3. **Cálculo e exclusión de Promedios**:
   * Ajuste de `_amount_prod_final()` y `compute_avg_score()` en `app.gradebook.student` para excluir del promedio las asignaturas cuyo código empieza por `NLEX` (case-insensitive).
   * Ajuste de los promedios cuatrimestrales calculados en `ap.gradebook.summary` para excluir materias NLEX.

4. **Exclusión en Reportes y Exportación SEP**:
   * Ocultación por medio de condicionales QWeb de las materias NLEX en la libreta de calificaciones (`report_gradebook`) y en el diploma certificado (`certified_diploma`).
   * Modificación de `action_export_to_dec()` en `app.gradebook.student` para evitar exportar asignaturas NLEX a la SEP y recalcular los totales de asignaturas y créditos consecuentemente.

---

## Pruebas Superadas

Se han ejecutado y superado las pruebas automáticas contenidas en `tests/test_nlex_grade_exemption.py`. Los siguientes casos han sido validados con éxito:
* **Fallo de validación para materias normales sin nota**: Verificación de que el sistema sigue requiriendo notas en asignaturas normales.
* **Cierre exitoso con NLEX sin nota**: Validación de que las libretas se cierran correctamente si la única materia pendiente es NLEX.
* **Ajuste de promedios final y general**: Comprobación de que las materias NLEX son excluidas de todas las medias y sumas.
* **Exclusión en archivos SEP (DEC)**: Verificación de que el XML de certificación exime a las materias NLEX de la lista de asignaturas y actualiza la cantidad de créditos correctos del alumno.

### Comando de ejecución de pruebas:
```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_nlex_grade_exemption --test-enable --test-tags=/irg_nlex_grade_exemption --stop-after-init
```
* **Resultado del test**: `0 failed, 0 error(s)` (Pruebas pasadas correctamente).

---

## v16.0.1.1.0 — Fix: exclusión NLEX en certificados de calificaciones (2026-06-12, tarde)

**Bug detectado:** las asignaturas NLEX seguían apareciendo en los certificados de calificaciones. La v1.0.0 solo parcheó las plantillas QWeb de `isep_gradebook` e `isep_openeducat_reports`, pero los certificados reales se generan por código Python en `irg_gradebook_certificates` e `irg_certificate_partial`, que filtraban asignaturas con su propia lambda (`subject_type == 'compulsory'`) sin exclusión NLEX.

**Cambios:**
* `irg_gradebook_certificates` (→ v16.0.1.0.1): nuevo hook `_get_certificate_subjects()` en `irg.certificate.request`; `_fill_template()` y la plantilla QWeb `report_certificate_document` lo usan en lugar del filtro inline.
* `irg_certificate_partial` (→ v16.0.1.0.1): `_fill_template()` reutiliza el hook (la nota media del parcial se calcula ya sobre asignaturas filtradas).
* `irg_nlex_grade_exemption` (→ v16.0.1.1.0): nuevo `models/irg_certificate_request.py` que sobrescribe el hook excluyendo códigos `NLEX*`; nueva dependencia `irg_gradebook_certificates`.

**Pruebas (TDD):**
* Test nuevo `test_certificate_subjects_exclude_nlex`: RED confirmado (AttributeError, hook inexistente) → GREEN tras implementación.
* Suite completa de los 3 módulos: `0 failed, 0 error(s) of 32 tests` en BD clonada `test_nlex_cert_tdd`.

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_nlex_cert_tdd \
  -u irg_nlex_grade_exemption,irg_gradebook_certificates,irg_certificate_partial \
  --test-enable --test-tags=/irg_nlex_grade_exemption,/irg_gradebook_certificates,/irg_certificate_partial \
  --stop-after-init
```

**Despliegue:** actualizar los 3 módulos (`-u irg_nlex_grade_exemption,irg_gradebook_certificates,irg_certificate_partial`).

---

## v16.0.1.2.0 — Generalización de la regla de exención NLEX → "contiene EX" (2026-06-15)

**Petición:** que la exención no se limite al prefijo `NLEX`, sino a cualquier asignatura marcada como exenta de forma más general.

**Decisión:** una asignatura es exenta cuando su código **contiene** la subcadena `EX` (case-insensitive). Cubre el caso legacy `NLEX*` y añade `*EX*` (p.ej. `MATEX01`, `ex03`).

**Cambios:**
* Nuevo `models/op_subject.py`: helper `op.subject.irg_is_grade_exempt()` como única fuente de verdad de la regla. Público (sin guion bajo) para poder llamarlo desde QWeb.
* Refactor: los 7 puntos que duplicaban `code.upper().startswith('NLEX')` ahora llaman al helper:
  - `app_gradebook_student.py` (state_to_done, _amount_prod_final, compute_avg_score, action_export_to_dec).
  - `ap_gradebook_summary.py` (promedio cuatrimestral).
  - `irg_certificate_request.py` (hook de certificados).
  - `views/report_gradebook.xml` y `views/certified_diploma.xml` (condiciones QWeb).

**Pruebas (TDD):**
* Test nuevo `test_exempt_rule_matches_any_ex_code`: verifica que `MATEX01` (no empieza por NLEX pero contiene EX) queda exento y excluido del certificado, que `NLEX01` sigue exento, y que un código sin EX no lo está.
* Suite completa de los 3 módulos: `0 failed, 0 error(s) of 33 tests` en BD clonada `test_nlex_ex_tdd`.

> ⚠️ Limitación conocida: códigos no exentos que contengan la subcadena `EX` (p.ej. `TEXTO01`, `FLEX02`) se marcarían como exentos por error. Evitar esos códigos o cambiar a marca explícita si surge el caso.

**Despliegue:** actualizar `irg_nlex_grade_exemption` (los otros dos módulos no cambian en esta versión).
