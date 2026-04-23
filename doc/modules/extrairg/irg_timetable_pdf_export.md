# irg_timetable_pdf_export

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `openeducat_timetable_enterprise`, `irg_op_session_class_title`

---

## ¿Qué hace este módulo?

Permite a los estudiantes descargar su calendario académico en formato PDF directamente desde el portal. Añade un botón de descarga en la vista del horario del portal que genera un informe PDF con todas las sesiones del alumno.

## Funcionalidades principales

- Botón "Descargar PDF" en la vista del calendario portal del alumno.
- Informe PDF QWeb con el horario académico del estudiante.
- Usa los títulos de sesión mejorados de `irg_op_session_class_title`.

## Vistas y UI

- `report/timetable_pdf_report.xml` — definición del informe QWeb PDF.
- `views/timetable_portal_pdf_button.xml` — botón de descarga en el portal.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_timetable_pdf_export \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_timetable_pdf_export \
    --stop-after-init --db_host=pgodoo_latest
```
