# irg_subscription_esp_single_invoice

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG
**Depende de:** `sale_subscription`, `isep_sale_subscription_extension`, `irg_sale_subscription_esp`, `isep_sale_order_cron_payment`, `irg_payment_stripe_recurring`

---

## ¿Qué hace este módulo?

Implementa una estrategia de facturación única para suscripciones, con ajustes futuros de cuotas. En lugar de generar una factura por cada cuota recurrente, genera una sola factura inicial y gestiona los ajustes de las cuotas posteriores mediante registros de ajuste.

## Funcionalidades principales

- Estrategia de factura única para suscripciones de pago en cuotas.
- Wizard para generar ajustes de cuotas manualmente.
- Registro de eventos Stripe para trazabilidad de cobros.
- Vista de ajustes de suscripción en el pedido de venta.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.subscription.adjustment` (nuevo) | Nuevo | Pedido, cuota, ajuste, estado |
| `irg.stripe.event` (nuevo) | Nuevo | ID evento Stripe, tipo, fecha, datos |
| `sale.order` | Herencia | Estrategia de facturación |
| `product.template` | Herencia | Configuración de facturación única |

## Vistas y UI

- `views/product_template_views.xml` — opción de facturación única en el producto.
- `views/sale_order_views.xml` — estado de ajustes en el pedido.
- `views/stripe_event_views.xml` — historial de eventos Stripe.
- `views/subscription_adjustment_views.xml` — gestión de ajustes.
- `wizards/subscription_adjustment_wizard_views.xml` — wizard de ajuste manual.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_subscription_esp_single_invoice \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_subscription_esp_single_invoice \
    --stop-after-init --db_host=pgodoo_latest
```
