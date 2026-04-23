# irg_google_calendar_sync_session_dedupe

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `irg_google_calendar_sync`, `openeducat_timetable`

---

## ¿Qué hace este módulo?

Evita la creación de eventos duplicados en Google Calendar al sincronizar sesiones académicas (`op.session`). Durante la sincronización, verifica si ya existe un evento de Google Calendar correspondiente a cada sesión antes de crear uno nuevo.

## Funcionalidades principales

- Lógica de deduplicación en la sincronización de `op.session` con Google Calendar.
- Verificación de existencia de evento antes de crear.
- Es dependencia de `irg_op_session_class_title`.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.session` | Herencia | Lógica de deduplicación en sync |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_google_calendar_sync_session_dedupe \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_google_calendar_sync_session_dedupe \
    --stop-after-init --db_host=pgodoo_latest
```
