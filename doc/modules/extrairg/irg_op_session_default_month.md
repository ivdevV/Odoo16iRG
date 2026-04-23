# irg_op_session_default_month

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `openeducat_timetable_enterprise`

---

## ¿Qué hace este módulo?

Configura la vista predeterminada del calendario de sesiones en el portal del estudiante para que se muestre en vista **mensual** en lugar de semanal. Esto mejora la experiencia del alumno al ver su horario completo del mes de un vistazo.

## Funcionalidades principales

- Script JavaScript que fuerza la vista mensual al cargar el calendario portal.
- Sin cambios de modelo; solo comportamiento frontend.

## Vistas y UI

Asset JS: `irg_op_session_default_month/static/src/js/portal_timetable_month_default.js`.

## Notas técnicas

- Requiere `security/ir.model.access.csv` (probablemente por una regla técnica relacionada con la herencia).

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_op_session_default_month \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_op_session_default_month \
    --stop-after-init --db_host=pgodoo_latest
```
