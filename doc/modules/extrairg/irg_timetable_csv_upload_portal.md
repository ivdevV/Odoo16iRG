# irg_timetable_csv_upload_portal

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** OPL-1
**Instalable:** Sí
**Autor:** Instituto Raimón Gaja
**Depende de:** `website`, `web`, `irg_timetable_csv_import`

---

## ¿Qué hace este módulo?

Proporciona una interfaz web (portal) para que los administradores puedan subir archivos CSV de calendarios académicos directamente desde el navegador, sin necesidad de acceso SSH al servidor. Extiende `irg_timetable_csv_import` con una capa de interfaz de usuario.

## Funcionalidades principales

- Formulario de subida de CSV accesible desde el portal web.
- Vista de gestión de archivos subidos en el backend.
- Integración con el sistema de importación de `irg_timetable_csv_import`.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.timetable.csv.upload` (nuevo) | Nuevo | Archivo CSV, fecha, estado, log |

## Vistas y UI

- `views/csv_upload_views.xml` — gestión en el backend.
- `views/portal_upload_template.xml` — formulario de subida en el portal web.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_timetable_csv_upload_portal \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_timetable_csv_upload_portal \
    --stop-after-init --db_host=pgodoo_latest
```
