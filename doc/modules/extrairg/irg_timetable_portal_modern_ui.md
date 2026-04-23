# irg_timetable_portal_modern_ui

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `openeducat_timetable_enterprise`

---

## ¿Qué hace este módulo?

Moderniza el diseño visual del calendario académico en el portal del estudiante. Reemplaza el aspecto predeterminado del horario de `openeducat_timetable_enterprise` con un diseño más limpio y moderno, mejorando la experiencia del alumno al consultar sus clases.

## Funcionalidades principales

- Override de templates del calendario portal para un diseño moderno.
- Estilos SCSS dedicados para el calendario del portal.
- Sin cambios de modelo o lógica de negocio; únicamente mejora visual.

## Vistas y UI

- `views/timetable_portal_overhaul.xml` — override de template del calendario portal.
- SCSS: `irg_timetable_portal_modern_ui/static/src/scss/portal_timetable_modern.scss`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_timetable_portal_modern_ui \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_timetable_portal_modern_ui \
    --stop-after-init --db_host=pgodoo_latest
```
