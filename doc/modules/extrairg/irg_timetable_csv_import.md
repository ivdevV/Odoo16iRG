# irg_timetable_csv_import

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `openeducat_timetable`

---

## ¿Qué hace este módulo?

Permite importar sesiones académicas (`op.session`) masivamente desde archivos CSV depositados en un directorio vigilado por el servidor. El módulo mapea etiquetas de programa de los CSV a los cursos y lotes de Odoo mediante una tabla de configuración, y crea las sesiones con deduplicación automática para evitar duplicados.

## Funcionalidades principales

- Importación masiva de sesiones de clase desde CSV.
- Tabla de mapeo de etiquetas de programa → curso/lote de Odoo (configurable desde el backend).
- Deduplicación automática al importar (no crea sesiones ya existentes).
- Cron automático que vigila el directorio y procesa nuevos archivos CSV.
- Log de importaciones con resultado de cada procesamiento.
- `post_init_hook` para configuración inicial.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.timetable.program.map` (nuevo) | Nuevo | Etiqueta CSV, curso Odoo, lote Odoo |
| `irg.timetable.import.log` (nuevo) | Nuevo | Fecha, archivo, estado, errores |

## Vistas y UI

- `views/program_map_views.xml` — gestión de la tabla de mapeo.
- `views/import_log_views.xml` — historial de importaciones.
- `views/menu.xml` — menú de acceso en el backend.

## Notas técnicas

- El directorio vigilado se configura mediante parámetros del sistema.
- Requiere `security/ir.model.access.csv` por sus modelos nuevos.
- El cron se define en `data/ir_cron.xml`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_timetable_csv_import \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_timetable_csv_import \
    --stop-after-init --db_host=pgodoo_latest
```
