# 2026-07-30 — `irg_stripe_payments`: listado de pagos de Stripe por contacto

Módulo nuevo en `addons-extra/extrairg/irg_stripe_payments`. **No modifica ningún módulo
existente.**

## Qué añade

- **`irg.stripe.payment`** — ledger local de pagos de Stripe, indexado por `stripe_id`
  (`pi_...`, o `ch_...` cuando no hay PaymentIntent). Vinculado a `res.partner`, y desde ahí a
  `op.student`, `sale.order`, `account.move` y `payment.transaction`.
- **`irg.stripe.identity.review`** — cola de revisión manual para los pagos cuyo contacto no
  se puede determinar sin ambigüedad.
- **Handlers de webhook** sobre el endpoint firmado ya existente (`/stripe/webhook`):
  `payment_intent.succeeded`, `payment_intent.payment_failed`, `charge.refunded` y
  `checkout.session.completed` en modo pago único. **No se crea ningún endpoint nuevo.**
- **Backfill histórico** paginando `charges`, con asistente (dry-run incluido) y cron
  resumible, desactivado por defecto.
- **Listado** en la pestaña Stripe de la ficha de contacto, stat button en la ficha de alumno,
  y menús *Pagos Stripe* / *Revisión de identidad* bajo Integración Stripe.

## Qué arregla

1. **Los pagos sueltos ya no se pierden.** `stripe.sync._sync_payment_intent_succeeded` salía
   por `return` cuando el PaymentIntent no llevaba factura de Stripe, es decir: Payment Links
   de pago único, cobros desde el Dashboard, Checkout puntual y Terminal no dejaban ningún
   rastro en Odoo.
2. **El matching por email ya no adivina.** La implementación previa hacía
   `search([('email','=ilike',...)], limit=1)` y escribía `irg_stripe_customer_id` sobre el
   primer contacto que saliera, sin filtrar archivados ni detectar duplicados.
   `res.partner.email` no tiene constraint de unicidad. Ahora: los archivados y fusionados
   quedan fuera, las direcciones hijas y las empresas se despriorizan, los alumnos van primero,
   y **ante más de un candidato no se elige ninguno**: se encola para revisión humana.
3. **El Customer ID ya no se sobrescribe.** El `write` era incondicional, así que un contacto
   con `cus_A` podía acabar apuntando a `cus_B` sin dejar rastro. Ahora ese caso se encola como
   `conflicting_customer_id` y no se escribe nada.

## Cambio de comportamiento a tener en cuenta

`stripe.sync._find_partner` conserva su firma, pero **ante ambigüedad devuelve un recordset
vacío en lugar de un contacto elegido al azar**. Consecuencia visible: pueden crearse registros
`stripe.subscription` con `partner_id` vacío, que antes salían asignados (a veces al contacto
equivocado). Los dos llamantes existentes ya toleraban el vacío.

Vía de escape sin redespliegue: `ir.config_parameter` `irg_stripe.email_match_mode` a `legacy`
restaura el comportamiento anterior; `disabled` desactiva el email por completo.

## Aviso al desinstalar

El endurecimiento de identidad vive en este módulo (override de `stripe.sync`). Desinstalarlo
devuelve el comportamiento antiguo de `limit=1`. Es la contrapartida aceptada de mantenerlo
todo en un solo módulo.

## Configuración

| Parámetro | Por defecto |
|---|---|
| `irg_stripe.email_match_mode` | `strict_unique` |
| `irg_stripe.backfill_max_days` | `92` |

## Validación

44/44 tests verdes en `scratch_stripe_payments` (clon de `test_irg_db`). Detalle en
`missions/irg-stripe-payments/03-validation.md`.

`test_10` de `irg_stripe_subscriptions` da error, **pero ya lo daba antes de esta misión**:
comprobado contra una base con el módulo base instalado y sin este módulo, con resultado
idéntico. Causa y arreglo documentados en el informe de validación.

## Pendiente antes de que esto reciba pagos reales

**Comprobar en el Dashboard de Stripe que `payment_intent.succeeded`,
`payment_intent.payment_failed`, `charge.refunded` y `checkout.session.completed` están
suscritos al endpoint `/stripe/webhook`.** Si no lo están, el módulo no recibirá nada.
