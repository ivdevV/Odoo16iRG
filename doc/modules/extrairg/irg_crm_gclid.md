# irg_crm_gclid

**Categoría:** extrairg
**Versión:** 16.0.1.0
**Licencia:** AGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `crm`

---

## ¿Qué hace este módulo?

Añade el campo `x_gclid` (Google Click ID) al modelo `crm.lead` para rastrear el origen de leads procedentes de campañas de Google Ads. El GCLID permite atribuir conversiones a campañas específicas en Google Analytics/Ads.

## Funcionalidades principales

- Campo `x_gclid` (Char) en `crm.lead` para almacenar el Google Click ID.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `crm.lead` | Herencia | `x_gclid` (Char) |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_crm_gclid \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_crm_gclid \
    --stop-after-init --db_host=pgodoo_latest
```
