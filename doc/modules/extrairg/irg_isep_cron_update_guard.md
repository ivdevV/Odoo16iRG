# irg_isep_cron_update_guard

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `web`, `isep_appointments`, `isep_payment_cron`, `isep_payment_cron_extend`

---

## ¿Qué hace este módulo?

Evita que los crons pesados de ISEP (cobros, citas) se ejecuten mientras hay operaciones de módulo en curso (instalaciones, actualizaciones). Muestra un indicador visual en la barra del sistema del backend cuando hay un proceso bloqueante activo.

## Funcionalidades principales

- Componente Systray en el backend que muestra el estado de procesos bloqueantes.
- Guard que pausa los crons de `isep_payment_cron`, `isep_payment_cron_extend` e `isep_appointments` durante actualizaciones.
- SCSS para el indicador visual.

## Vistas y UI

- JS: `irg_isep_cron_update_guard/static/src/js/blocking_process_systray.js`.
- XML Owl: `irg_isep_cron_update_guard/static/src/xml/blocking_process_systray.xml`.
- SCSS: `irg_isep_cron_update_guard/static/src/scss/blocking_process_systray.scss`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_isep_cron_update_guard \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_isep_cron_update_guard \
    --stop-after-init --db_host=pgodoo_latest
```
