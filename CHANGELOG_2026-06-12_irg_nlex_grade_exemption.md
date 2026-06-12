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
