# irg_tfm_acta_documento

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** AGPL-3
**Instalable:** Sí
**Autor:** ISEP / iRG
**Depende de:** `base`, `web`, `website`, `openeducat_core`, `irg_generacion_diplomas`

---

## ¿Qué hace este módulo?

Genera actas de evaluación de Trabajos Finales de Máster (TFM) y Grado (TFG) desde la ficha del estudiante. El módulo permite capturar datos del tribunal, la titulación y el trabajo, y generar un PDF con campos editables para la fecha de defensa, calificación, observaciones y firma del secretario.

## Funcionalidades principales

- Wizard de generación de actas desde `op.student`.
- Modelo `irg.tfm.acta` para registrar actas y adjuntar el PDF generado.
- Descarga directa del PDF generado desde la ficha del acta.
- Plantilla PDF construida con ReportLab.
- Diseño compatibilizado con los logos y fuentes de `irg_generacion_diplomas`.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.tfm.acta` | Nuevo | Estudiante, tipo, grado, tribunal, defensa, calificación, observaciones, attachment |
| `irg.tfm.acta.wizard` | Nuevo | Wizard de generación de actas desde `op.student` |

## Vistas y UI

- `views/acta_views.xml` — lista y formulario de actas.
- `wizard/acta_wizard_views.xml` — formulario de wizard para generar el acta.
- Herencia en la vista de estudiante para abrir el wizard desde `openeducat_core.view_op_student_form`.

## Notas técnicas

- Usa `reportlab` para generar PDF desde Python.
- Reutiliza el logo y las fuentes de `irg_generacion_diplomas`.
- Incluye el paquete Python `reports` con el modelo `report.irg_tfm_acta_documento.acta_pdf`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_tfm_acta_documento \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_tfm_acta_documento \
    --stop-after-init --db_host=pgodoo_latest
```
