# irg_batch_homeclass_subject_lead_days

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí (instalación explícita; `auto_install` False)
**Autor:** iRG
**Depende de:** `irg_batch_homeclass_api_scheduler`

---

## ¿Qué hace este módulo?

Tras un sync exitoso del scheduler HomeClass, adelanta **3 días** el
`date_from` de cada asignatura del lote. El campus y el auto-enroll se abren
antes de la primera clase del calendario. La fecha oficial de inicio de clases
del lote (`date_start_class`) y el `date_to` de cada línea no cambian.

## Funcionalidades principales

- Hereda `op.batch` y redefine `_sync_homeclass_calendar`.
- Llama a `super()` (API, matching, fallback, `date_to`, `date_start_class`).
- Si el sync original falla, no reescribe fechas.
- Si tiene éxito, resta 3 días a cada `date_from` informado (match de API y
  fallback a `start_date`).
- Un segundo sync no acumula el offset: el padre vuelve a escribir la fecha
  absoluta y después se restan 3 días.

## Modelos

| Modelo | Tipo | Campos / comportamiento |
|--------|------|-------------------------|
| `op.batch` | Herencia | `_irg_apply_homeclass_subject_lead_days()`; offset `IRG_HOMECLASS_SUBJECT_LEAD_DAYS = 3` |

No crea modelos nuevos ni vistas.

## Tests

`tests/test_subject_lead_days.py`, etiquetados `post_install` y `-at_install`.
Parchean `requests.get` del scheduler y crean lotes con `skip_homeclass_sync`.

- Match API: 16/01/2026 → 13/01/2026; `date_to` y `date_start_class` intactos.
- Fallback `start_date` 01/01/2026 → 29/12/2025 (sin recorte).
- `date_from` vacío no se toca.
- Sync fallida deja las fechas como estaban.
- Dos syncs seguidas no restan 6 días.

## Limitaciones

- El scheduler original no se modifica. Matching, fallback y ausencia de cron
  siguen igual.
- Hay que instalar el módulo en cada entorno; no se autoinstala.
- Un `date_from` puede quedar anterior a `start_date` del lote.

## Instalación / Actualización

```bash
docker compose -f docker-compose.local.yml run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d <dbname> \
  -i irg_batch_homeclass_subject_lead_days \
  --stop-after-init --http-port=8099
```
