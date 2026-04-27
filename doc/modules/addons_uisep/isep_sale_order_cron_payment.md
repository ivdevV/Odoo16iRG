# isep_sale_order_cron_payment

**Categoría:** addons_uisep
**Versión:** 16.1
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `base`, `sale`, `payment`, `account`, `account_edi`, `sms`, `sale_subscription`

---

## ¿Qué hace este módulo?

Gestiona la creación automática de facturas de suscripción con días de anticipación configurables. El cron revisa los pedidos de suscripción activos y genera las facturas correspondientes antes de la fecha de vencimiento, según el parámetro de anticipación definido en la configuración.

También envía SMS de aviso al alumno antes del cobro.

## Funcionalidades principales

- Cron de facturación anticipada de suscripciones.
- Generación automática de `account.move` desde `sale.order` de suscripción.
- Envío de SMS de aviso antes del cobro.
- Parámetro de días de anticipación configurable.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `sale.order` | Herencia | Lógica de facturación anticipada |

## Notas técnicas

- La configuración de días de anticipación se hace en Ajustes → Parámetros del sistema.
- El cron usa `account_edi` para la correcta generación de facturas electrónicas.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_sale_order_cron_payment \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_sale_order_cron_payment \
    --stop-after-init --db_host=pgodoo_latest
```
