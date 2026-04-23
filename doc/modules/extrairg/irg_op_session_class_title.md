# irg_op_session_class_title

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `isep_op_session`, `irg_google_calendar_sync_session_dedupe`

---

## ¿Qué hace este módulo?

Muestra el nombre de la clase (classroom) en las tarjetas de eventos del calendario de sesiones del portal. Sin este módulo, los eventos solo muestran el nombre de la asignatura; con él se añade el nombre del aula/clase para que el alumno sepa en qué sala tiene cada clase.

## Funcionalidades principales

- Añade el nombre de clase (aula) al título o subtítulo de cada tarjeta de sesión en el calendario.
- Es dependencia de `irg_timetable_pdf_export` y `irg_timetable_session_title_endpoint`.

## Notas técnicas

- Sin archivos de datos propios (`data: []`).

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_op_session_class_title \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_op_session_class_title \
    --stop-after-init --db_host=pgodoo_latest
```
