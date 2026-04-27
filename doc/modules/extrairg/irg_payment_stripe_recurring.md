# irg_payment_stripe_recurring

**Categoría:** extrairg
**Versión:** 16.0.2.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `payment_stripe`, `sale_subscription`, `isep_sale_subscription_extension`, `isep_payment_cron`

---

## ¿Qué hace este módulo?

Extiende el proveedor de pago Stripe para soportar cobros recurrentes y suscripciones nativas. Es el módulo que gestiona el ciclo de vida completo de los pagos recurrentes con Stripe: desde la asignación del token tras el primer pago hasta la suspensión/reactivación automática por deudas vencidas.

## Funcionalidades principales

- Asignación automática del token Stripe a la suscripción tras el primer pago.
- Creación de suscripciones nativas en Stripe (modo `stripe_subscription_real`).
- Sincronización de pausa, reactivación y cancelación con la API de Stripe.
- Webhook handler para eventos de suscripción Stripe (eventos de pago, fallo, etc.).
- Cron de suspensión automática por cuotas vencidas impagadas.
- Cron de reactivación automática cuando se saldan deudas.
- Plantillas de email para notificaciones de estado de pago.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `payment.provider` | Herencia | Campos de configuración Stripe recurring |
| `sale.order` | Herencia | Estado de suscripción Stripe, token asignado |
| `res.partner` | Herencia | Token Stripe del cliente |

## Vistas y UI

- `views/sale_order_views.xml` — estado de suscripción Stripe en el pedido.
- `views/res_partner_views.xml` — token Stripe del cliente.

## Notas técnicas

- Usa `sudo()` en el webhook handler (justificado: el webhook llega sin sesión de usuario).
- El webhook debe estar registrado en el panel de Stripe y configurado en Odoo.
- Requiere `security/ir.model.access.csv`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_payment_stripe_recurring \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_payment_stripe_recurring \
    --stop-after-init --db_host=pgodoo_latest
```
