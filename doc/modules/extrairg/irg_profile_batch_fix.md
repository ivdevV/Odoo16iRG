# irg_profile_batch_fix

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `isep_website_custom`, `isep_website_custom_design`, `irg_course_portal_tiles`, `isep_time_link_url`

---

## ¿Qué hace este módulo?

Corrige dos problemas en el panel de campus del alumno:

1. **Nombre incorrecto** en las tarjetas del programa: las tarjetas mostraban el nombre del lote en lugar del nombre del programa/curso.
2. **Filtro de calendario**: el botón del calendario ahora filtra las sesiones por el lote del alumno, no mostrando todo el calendario del curso.

También incluye un componente JavaScript para el filtrado de calendario por lote.

## Funcionalidades principales

- Corrección del nombre en las tarjetas del programa de campus.
- Filtrado automático del calendario de sesiones por lote del alumno.

## Vistas y UI

- `views/campus_profile_cards.xml` — override de las tarjetas del programa.

## Notas técnicas

- JS: `static/src/js/timetable_batch_filter.js`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_profile_batch_fix \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_profile_batch_fix \
    --stop-after-init --db_host=pgodoo_latest
```
