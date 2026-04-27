# isep_payment_cron

**Categoría:** addons_uisep
**Versión:** 7.0
**Licencia:** No especificada
**Instalable:** Sí
**Autor:** ISEP
**Depende de:** `sale_subscription`, `base_automation_webhook`, `base_automation`

---

## ¿Qué hace este módulo?

Procesa cobros recurrentes tokenizados mediante Stripe. A través de un cron, intenta cobrar los tokens de pago guardados del alumno para las cuotas pendientes de suscripción, actualizando el estado de la factura y notificando al alumno del resultado.

Es el componente de ejecución de cobros del sistema de financiación, trabajando en conjunto con `isep_sale_subscription_extension` (que planifica los cobros) y `isep_sale_order_cron_payment` (que genera las facturas).

## Funcionalidades principales

- Cron de cobro recurrente con token de pago Stripe.
- Procesamiento de transacciones tokenizadas.
- Actualización del estado de factura tras el cobro.
- Notificación al alumno del resultado del cobro.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `payment.token` | Herencia | Uso en cobros recurrentes |
| `sale.subscription` | Herencia | Lógica de cobro por cron |

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i isep_payment_cron \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_payment_cron \
    --stop-after-init --db_host=pgodoo_latest
```
