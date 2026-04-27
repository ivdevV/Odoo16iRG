# irg_timetable_irg_api

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `openeducat_timetable_enterprise`

---

## ¿Qué hace este módulo?

Implementa el calendario portal estudiantil consumiendo datos desde la **API externa de Calendarios IRG** en lugar de leer directamente de la base de datos de Odoo. Este módulo es el núcleo del sistema de horarios del campus: el frontend JavaScript hace llamadas a la API IRG para obtener las sesiones de clase del alumno.

## Funcionalidades principales

- Template portal que renderiza un calendario vacío que se puebla dinámicamente vía API.
- Cliente JavaScript que consume la API externa de Calendarios IRG.
- Estilos SCSS para la vista del calendario API.
- Permite desacoplar los datos del horario de Odoo y servirlos desde un sistema externo.

## Vistas y UI

- `views/portal_template.xml` — template base del calendario portal.
- JS: `irg_timetable_irg_api/static/src/js/irg_timetable_api.js`.
- SCSS: `irg_timetable_irg_api/static/src/scss/irg_timetable_api.scss`.

## Notas técnicas

- Es la dependencia base de `irg_timetable_lote_batch_fix` y `irg_timetable_session_title_endpoint`.
- La URL de la API externa se debe configurar en los parámetros del sistema.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_timetable_irg_api \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_timetable_irg_api \
    --stop-after-init --db_host=pgodoo_latest
```
