# irg_timetable_portal_overhaul_v2

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `openeducat_timetable_enterprise`

---

## ¿Qué hace este módulo?

Realiza un overhaul estructural completo del calendario portal estudiantil, versión 2. Mientras `irg_timetable_portal_modern_ui` aplica mejoras visuales, este módulo reestructura la arquitectura del template del calendario, con cambios más profundos en la organización del HTML y la lógica JavaScript de interacción.

## Funcionalidades principales

- Reestructuración completa del HTML del calendario portal.
- Lógica JavaScript renovada para la interacción con el calendario.
- Estilos SCSS específicos de la versión 2.

## Vistas y UI

- `views/timetable_portal_overhaul_v2.xml` — override estructural del template.
- JS: `static/src/js/portal_timetable_overhaul_v2.js`.
- SCSS: `static/src/scss/portal_timetable_overhaul_v2.scss`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_timetable_portal_overhaul_v2 \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_timetable_portal_overhaul_v2 \
    --stop-after-init --db_host=pgodoo_latest
```
