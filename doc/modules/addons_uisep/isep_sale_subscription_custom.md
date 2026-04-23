# isep_sale_subscription_custom

**Categoría:** addons_uisep
**Versión:** 16.0.2
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `base`, `sale_subscription`, `sales_team`, `account`, `sale`, `web`, `report_xlsx`, `web_grid`, `isep_openeducat_sale`

---

## ¿Qué hace este módulo?

Módulo base de personalización del sistema de suscripciones de ISEP. Establece la estructura base del sistema de pagos a plazos: campos de configuración de cuotas, frecuencias de pago y los cimientos del calendario de pagos que luego extiende `isep_sale_subscription_extension`.

## Funcionalidades principales

- Campos base de configuración de suscripción en `sale.order`.
- Tipos de recurrencia y frecuencias de pago.
- Estructura base del calendario de pagos.
- Integración con el sistema de suscripciones de Odoo.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `sale.order` | Herencia | Campos de suscripción y pago a plazos |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_sale_subscription_custom \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_sale_subscription_custom \
    --stop-after-init --db_host=pgodoo_latest
```
