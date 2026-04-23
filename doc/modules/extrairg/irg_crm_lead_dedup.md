# irg_crm_lead_dedup

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** AGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `crm`

---

## ¿Qué hace este módulo?

Implementa un cron diario que detecta y fusiona automáticamente leads duplicados en el CRM, identificando duplicados por email o número de teléfono. Reduce la base de datos de leads y evita que el equipo comercial trabaje con información fragmentada.

## Funcionalidades principales

- Cron diario de deduplicación de leads.
- Detección de duplicados por email y teléfono.
- Fusión automática de leads duplicados.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `crm.lead` | Herencia | Lógica de deduplicación |

## Notas técnicas

- El cron se define en `data/cron.xml`.
- La fusión usa la lógica nativa de Odoo de merge de leads.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_crm_lead_dedup \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_crm_lead_dedup \
    --stop-after-init --db_host=pgodoo_latest
```
