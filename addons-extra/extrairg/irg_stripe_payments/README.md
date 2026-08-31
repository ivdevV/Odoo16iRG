# IRG - Stripe Payments Ledger

Listado de pagos de Stripe por contacto / alumno.

## Qué problema resuelve

La integración Stripe previa (`irg_payment_stripe_recurring` + `irg_stripe_subscriptions`)
cubre bien las **suscripciones**, pero deja tres huecos que impiden tener un listado de
pagos por persona:

1. **Los pagos sueltos se descartan en silencio.** `stripe.sync._sync_payment_intent_succeeded`
   sale por `return` cuando el PaymentIntent no lleva `invoice` de Stripe. Es decir: Payment
   Links de pago único, cobros creados desde el Dashboard, Checkout puntual y Terminal no
   dejan ningún rastro en Odoo. No existía ningún modelo local de charges/payment intents.
2. **El matching por email podía vincular al contacto equivocado.** La implementación previa
   hacía `search([('email','=ilike',...)], limit=1)` y acto seguido escribía
   `irg_stripe_customer_id` sobre el primero que saliera, sin filtrar `active`/`type` ni
   detectar ambigüedad. `res.partner.email` no tiene constraint de unicidad en ninguna parte.
3. **No había backfill.** Los pagos históricos nunca se trajeron.

## Invariante (importante)

> `irg.stripe.payment` es un **ledger de SOLO LECTURA**.
>
> Nunca escribe `sale.note.inv.legacy`, nunca toca `sale.subscription.schedule`, nunca crea
> `account.move` ni `account.payment`, nunca muta campos de dinero de `sale.order`.
>
> La conciliación monetaria sigue siendo exclusiva de `_sync_invoice_paid` /
> `_register_paid_invoice_on_schedule` en `irg_stripe_subscriptions`.

Esto es lo que hace **estructuralmente imposible** el doble conteo: el ledger observa y
enlaza, no concilia.

## Resolución de identidad

Escalera, de más fiable a menos:

1. `payment.transaction.provider_reference == pi_...` → `tx.partner_id` (pagos que pasaron
   por el checkout del portal; la señal más fuerte).
2. `client_reference_id` (`odoo_partner_<id>` / `odoo_order_<id>`) y `metadata.odoo_partner_id`
   / `metadata.odoo_order_id`.
3. `res.partner.irg_stripe_customer_id` / `stripe_customer_id`.
4. `GET customers/{cid}` → `metadata.odoo_partner_id`.
5. Email — **solo si es inequívoco**. Alumnos (`op.student`) primero. Si hay más de un
   candidato, **no se elige ninguno**: se encola en `irg.stripe.identity.review` para
   decisión humana.

Guarda de escritura: nunca se sobrescribe un `irg_stripe_customer_id` ya existente y distinto;
ese caso se encola como `conflicting_customer_id`.

Kill switch: `ir.config_parameter` `irg_stripe.email_match_mode` ∈
`strict_unique` (por defecto) | `disabled` | `legacy`.

## Aviso al desinstalar

El endurecimiento de la resolución de identidad vive en este módulo (override de
`stripe.sync._find_partner`). **Desinstalarlo devuelve el comportamiento antiguo de
`limit=1`**, que puede vincular pagos al contacto equivocado. Es la contrapartida aceptada de
mantenerlo todo en un solo módulo.

## Configuración

| Parámetro | Por defecto | Para qué |
|---|---|---|
| `irg_stripe.email_match_mode` | `strict_unique` | Cómo tratar el matching por email |
| `irg_stripe.backfill_max_days` | `92` | Ventana máxima por ejecución de backfill |
| `irg_stripe.backfill_cursor` | — | Cursor `starting_after` persistido (reanudación) |

## Notas de implementación no obvias

- `payment.provider._stripe_make_request` manda `payload` como **body** (`data=`), así que en
  peticiones `GET` los query params tienen que ir **en el string del endpoint**.
- `_stripe_make_request` **lanza `ValidationError`** ante un 4xx (incluido 429); no devuelve
  `{'error': ...}`. Los `if not res.get('error')` del código previo son medio código muerto.
- La versión de API de los payloads de **webhook** la fija el endpoint en el Dashboard de
  Stripe, y puede diferir de la de las llamadas API. Por eso los extractores de este módulo
  (`_pi_charge_id`, `_pi_email`, ...) son agnósticos de forma y miran tanto
  `charges.data[0]` como `latest_charge`.
