# irg_timetable_lote_batch_fix

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `irg_timetable_irg_api`

---

## ¿Qué hace este módulo?

Corrige la resolución del lote (batch) en la URL `/student/timetable/?batch_id=X`. Cuando la URL incluye un parámetro `batch_id`, el módulo usa ese batch directamente para mostrar el horario, en lugar de usar el primer enrollment "running" que puede ser incorrecto para alumnos con múltiples programas activos simultáneamente.

## Funcionalidades principales

- Parche JavaScript que intercepta la inicialización del calendario API.
- Lee el parámetro `batch_id` de la URL y lo pasa directamente a la API.
- Evita que alumnos con varios programas activos vean el horario equivocado.

## Notas técnicas

- Solo archivo JS (`static/src/js/timetable_lote_batch_fix.js`); sin cambios de modelo.
- Registrado en `web.assets_frontend`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_timetable_lote_batch_fix \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_timetable_lote_batch_fix \
    --stop-after-init --db_host=pgodoo_latest
```
