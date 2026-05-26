# irg_stripe_subscriptions

**Categoría:** extrairg  
**Versión:** 16.0.1.0.0  
**Licencia:** LGPL-3  
**Instalable:** Sí  
**Autor:** Instituto Raimon Gaja  
**Depende de:** `sale`, `payment`, `mail`, `irg_payment_stripe_recurring`

---

## ¿Qué hace este módulo?

Este módulo implementa el backend y frontend de sincronización completa para las **Suscripciones** y **Enlaces de Pago fijos** (Payment Links) de Stripe en Odoo 16. 

A diferencia de `irg_payment_stripe_recurring` (que actúa principalmente como puente post-pago para tokenizar tarjetas y disparar cobros directos de Odoo a Stripe), `irg_stripe_subscriptions` define modelos locales dedicados para almacenar, visualizar e interactuar directamente con los objetos de Stripe (`Customer`, `Subscription`, `PaymentLink`). Adicionalmente, expone un endpoint público de webhook `/stripe/webhook` con firma e idempotencia para actualizar estos registros en tiempo real tras eventos en la plataforma Stripe.

---

## Funcionalidades principales

1. **Suscripciones Stripe Locales (`stripe.subscription`)**: Almacena las suscripciones nativas (`sub_...`) del cliente, su estado, importes, intervalos y vigencia de período de facturación actual.
2. **Enlaces de Pago Fijos (`stripe.payment.link`)**: Almacena los enlaces de pago reutilizables creados en Stripe (`plink_...`) permitiendo visualizarlos y asociarlos directamente a los presupuestos.
3. **Log de Eventos e Idempotencia (`stripe.event.log`)**: Registra cada evento recibido desde Stripe (`evt_...`) y bloquea ejecuciones duplicadas de webhooks a nivel de base de datos.
4. **Endpoint de Webhook Público `/stripe/webhook`**:
   - Valida la autenticidad del evento usando `stripe.Webhook.construct_event()` y el secret de firma de Stripe (`whsec_...`).
   - Soporta eventos de creación, actualización y cancelación de suscripciones, así como confirmaciones de checkout de Payment Links.
5. **Acciones en Presupuestos (`sale.order`)**:
   - Generación directa de un cliente en Stripe.
   - Creación de una suscripción nativa desde la orden.
   - Generación de un Payment Link fijo de Stripe para la suscripción, asociándolo de forma persistente y mostrando su URL en el presupuesto.
6. **Sincronización con Suscripciones Nativas y Wizard**:
   - Se integra con `irg_sale_manual_confirmation_wizard` y `irg_payment_stripe_recurring` interceptando la creación/edición de suscripciones para que persistan y vinculen de inmediato el registro en `stripe.subscription`.
   - Si la suscripción de Stripe se actualiza (ej. cancelada o pausada) vía webhook, suspende/reactiva automáticamente la suscripción nativa de Odoo (`sale.order.subscription_suspended` y estado).

---

## Modelos Modificados y Creados

| Modelo | Tipo | Descripción |
|--------|------|-------------|
| `stripe.subscription` | Nuevo | Almacena y gestiona las suscripciones reales (`sub_...`). |
| `stripe.payment.link` | Nuevo | Almacena los enlaces de pago fijos (`plink_...`). |
| `stripe.event.log` | Nuevo | Registro para idempotencia de eventos (`evt_...`). |
| `stripe.sync` | Nuevo | Servicio abstracto con la lógica de emparejamiento de partners y parsing de payloads. |
| `res.partner` | Herencia | Agrega One2many con suscripciones, Many2many con enlaces de pago y `stripe_customer_id`. |
| `sale.order` | Herencia | Redefine `stripe_subscription_id` como Many2one y añade `stripe_payment_link_id`. |
| `payment.transaction` | Herencia | Adapta el método `_irg_maybe_create_stripe_subscription` para evitar fallos de AttributeError al operar con el nuevo campo Many2one. |
| `res.config.settings` | Herencia | Añade la configuración global en Odoo para credenciales y versión de API de Stripe. |

---

## Configuración Técnica

Los parámetros requeridos se configuran desde la pantalla de Ventas o Ajustes Generales de Odoo:

- **`stripe.api_key`**: Secret API Key (`sk_live_...` / `sk_test_...`).
- **`stripe.publishable_key`**: Publishable API Key (`pk_...`).
- **`stripe.webhook_secret`**: Firma de webhook (`whsec_...`).
- **`stripe.api_version`**: Opcional, fija la versión para evitar breaking changes (ej: `2025-06-30.basil`).

---

## Capa de Compatibilidad de Tipos (Many2one ↔ String)

Dado que los módulos previos (como `irg_payment_stripe_recurring`) definen `stripe_subscription_id` en `sale.order` como un campo de texto plano (Char), este módulo implementa un interceptor inteligente en los métodos `create` y `write` de `sale.order`. 

Si algún proceso escribe una cadena (ej. `"sub_12345"`) en dicho campo, el interceptor:
1. Captura la cadena.
2. Busca o crea un registro `stripe.subscription` con ese ID de Stripe.
3. Reemplaza el valor en la cola de escritura con el ID entero del registro Many2one.

Esto previene errores de incompatibilidad en base de datos.

---

## Flujos de Webhook Sincronizados

- **`customer.subscription.created` / `customer.subscription.updated`**:
  - Crea o actualiza `stripe.subscription`.
  - Mapea importes de centavos a decimales.
  - Sincroniza el estado hacia el presupuesto de Odoo (`sale.order.stripe_subscription_state`).
  - Pausa o reanuda el presupuesto nativo (`subscription_suspended`) en base a los estados de Stripe (`paused`, `active`, `past_due`).
- **`customer.subscription.deleted`**:
  - Marca `stripe.subscription` local como `canceled`.
  - Desactiva renovación en Odoo (`sale.order.to_renew = False`), suspende el pedido (`subscription_suspended = True`) y deja nota en el chatter.
- **`checkout.session.completed`**:
  - Se ejecuta cuando el cliente finaliza el flujo de pago en Stripe.
  - Identifica al partner comercial en Odoo usando `client_reference_id` (que contiene `"odoo_order_<id>"` u `"odoo_partner_<id>"`).
  - Guarda el ID del cliente Stripe en el partner de Odoo y vincula la suscripción creada.

---

## Pruebas y Validación

La cobertura automatizada se encuentra en `tests/test_stripe_subscriptions.py`. Valida:
- Interceptación y conversión de String a Many2one ID.
- Control de unicidad e idempotencia en `stripe.event.log`.
- Creación de suscripciones e inyección en presupuestos mediante simulación de webhooks.
- Cancelación automática de suscripciones Odoo tras recibir el evento de Stripe delete.

Para correr los tests en el Docker local:
```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db -u irg_stripe_subscriptions \
    --test-enable --test-tags /irg_stripe_subscriptions \
    --stop-after-init
```

---

## Instalación / Actualización en Local

```bash
# Instalación inicial
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db -i irg_stripe_subscriptions --stop-after-init

# Actualización
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db -u irg_stripe_subscriptions --stop-after-init
```

---

## Historial de Cambios

- **2026-05-26**: Creación inicial del módulo `irg_stripe_subscriptions` con soporte para modelos nativos Stripe, sincronización bidireccional por webhook idempotente, compatibilidad de tipos (Char a Many2one) con `irg_payment_stripe_recurring`, y suite de pruebas unitarias integradas.
