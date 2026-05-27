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

En el flujo actual, la creación de la suscripción nativa ya no se resuelve con una API auxiliar específica del módulo, sino delegando en el puente canónico de `sale.order` (`sale.order._irg_create_stripe_subscription()`), para mantener una sola vía de creación y sincronización.

## Funcionalidades principales

- Asignación automática del token Stripe a la suscripción tras el primer pago.
- Creación de suscripciones nativas en Stripe desde el puente canónico de `sale.order` (modo `stripe_subscription_real`).
- Idempotencia por `stripe_subscription_id` o `stripe_subscription_ref` con prefijo `sub_`.
- Idempotencia estable por pedido en `stripe_subscription_bridge.py` con la clave `irg_sub_<sale_order.id>`, para evitar duplicados en reintentos separados.
- Sincronización de `stripe_subscription_id`, `stripe_subscription_ref` e `irg_stripe_bridge_state` cuando la suscripción se crea con éxito.
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

## Flujo Stripe post-pago

La creación de la suscripción nativa se dispara después de que la transacción Stripe quede en estado `done` y el pedido asociado sea una suscripción.

1. `payment.transaction._reconcile_after_done()` mantiene la cadena estándar de reconciliación y después ejecuta el post-procesado de Stripe.
2. Si el pedido aún no tiene una suscripción Stripe creada, `_irg_maybe_create_stripe_subscription()` delega en `sale.order._irg_create_stripe_subscription()`.
3. Antes de crear, el módulo comprueba idempotencia con `stripe_subscription_id` o `stripe_subscription_ref`; si alguno ya apunta a un identificador `sub_...`, la creación se omite.
4. El puente Stripe usa además una idempotency key estable por pedido, `irg_sub_<sale_order.id>`, en lugar de una clave basada en timestamp.
5. En modo `stripe_subscription_real` se exige un token con `stripe_payment_method`. En `payment_link_fallback`, el flujo puede continuar sin método de pago local.
6. Si la creación devuelve `sub_id`, el módulo sincroniza los campos de puente disponibles en el pedido: `stripe_subscription_id`, `stripe_subscription_ref` e `irg_stripe_bridge_state`.

Este comportamiento concentra la lógica en el modelo de pedido y evita duplicidades entre transacciones, tokens y suscripciones nativas.

## Pruebas

La cobertura automatizada del cambio está en `addons-extra/extrairg/irg_payment_stripe_recurring/tests/` y valida:

- delegación al método canónico de `sale.order`,
- bloqueo de duplicados cuando ya existe una suscripción Stripe,
- uso de una idempotency key estable por pedido en el puente Stripe,
- exigencia de token y `stripe_payment_method` en `stripe_subscription_real`,
- continuidad sin token en `payment_link_fallback`,
- coherencia del estado bridge tras una creación satisfactoria.

Validación local ejecutada con Odoo:

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_payment_stripe_recurring --test-enable --test-tags /irg_payment_stripe_recurring --stop-after-init
```

Resultado: `0 failed, 0 error(s) of 8 tests`.

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

## Historial reciente

- **2026-05-22:** se actualizó el flujo de creación Stripe post-pago para delegar en `sale.order._irg_create_stripe_subscription()`, reforzar la idempotencia con `stripe_subscription_id` / `stripe_subscription_ref`, usar una idempotency key estable por pedido (`irg_sub_<sale_order.id>`), sincronizar el estado bridge cuando la creación tiene éxito y documentar la validación local del módulo.
