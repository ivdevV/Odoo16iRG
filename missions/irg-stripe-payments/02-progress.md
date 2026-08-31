# 02 — Progreso

Rama: `feat/irg-stripe-payments` (desde `Dev_iRG` actualizado a `86e1920ef`).
Entorno: **solo local** (`docker-compose.local.yml`). Ninguna conexión a producción ni al
servidor de beta. BD de trabajo: `scratch_stripe_payments`, clon de `test_irg_db`.

## Fase 0 — Recon

Cerrado leyendo `payment_stripe` dentro del contenedor
(`/usr/lib/python3/dist-packages/odoo/addons/payment_stripe/`). Los cuatro supuestos del
plan quedan confirmados, y dos de ellos con matiz:

| Supuesto | Resultado |
|---|---|
| Versión de API | `Stripe-Version: 2019-05-16`, **hardcodeada** en `const.py:6`. El parámetro `stripe.api_version` de los ajustes de `irg_stripe_subscriptions` no lo lee nadie. |
| Query params en GET | `payment_provider.py:269` → `requests.request(method, url, data=payload, ...)`. `payload` viaja como **body**, que Stripe ignora en un GET. Confirmado: la paginación tiene que ir en el string del endpoint. |
| 4xx lanza | `payment_provider.py:275-289`: lanza `ValidationError` **solo** si el 4xx trae `error` en el JSON y la operación no es `offline`. Un 5xx **no** lanza: devuelve el JSON tal cual. Un `ConnectionError` sí lanza. |
| Forma del charge | Con 2019-05-16 la API devuelve `charges.data[...]`; `latest_charge` es de 2022-08-01. Como el payload de webhook usa la versión del *endpoint* del Dashboard, ambas formas son posibles. |

Consecuencia de diseño: `_fetch_page` hace las dos cosas —capturar la excepción y mirar
`res.get('error')`—, porque ninguna de las dos por separado cubre todos los fallos. Y los
extractores (`_pi_charge`, `_pi_charge_id`, `_pi_invoice_id`, `_pi_email`) son agnósticos de
forma.

**T0.2 y T0.3 quedan pendientes** y no bloquean el código:
- T0.2 (censo de emails duplicados) hay que medirlo sobre datos reales, no sobre un clon de test.
- T0.3 (qué eventos están suscritos en cada endpoint del Dashboard de Stripe) requiere acceso
  al Dashboard. **Es un paso de despliegue**: si `payment_intent.succeeded` no está enrutado a
  `/stripe/webhook`, el módulo no recibirá nada hasta añadirlo.

## Fases 1-5 — Implementación

Módulo nuevo `addons-extra/extrairg/irg_stripe_payments`, 23 ficheros. **Cero cambios en
módulos existentes.**

- `irg.stripe.payment` — ledger idempotente. Clave `stripe_id` = `pi_...` o, si no hay
  PaymentIntent, `ch_...`. Upsert *merge, no clobber*: no pisa campos no vacíos con vacíos y
  no degrada `partner_match_method` a un método de menor confianza (tabla `MATCH_CONFIDENCE`).
- `irg.stripe.identity.review` — cola de revisión con deduplicación por
  `(stripe_object_id, reason, state=open)` y `occurrence_count`.
- `stripe.sync` (herencia) — `_resolve_partner` / `_find_partner` endurecidos,
  `_irg_identify_payment` con escalera de 4 niveles, y handlers de
  `payment_intent.succeeded`, `payment_intent.payment_failed`, `charge.refunded` y
  `checkout.session.completed`.
- `irg.stripe.backfill` — motor paginado sobre `charges`, con backoff, cursor persistido y
  dry-run.
- Vistas: tree/form/search/pivot/graph, pestaña Stripe en `res.partner`, stat button en
  `op.student`, y menús bajo *Integración Stripe*.

## Desviaciones respecto al plan aprobado

1. **Dependencias.** El plan proponía depender de `irg_partner_openeducat_info` para
   reutilizar `partner.student_id`. Ese módulo arrastra `isep_student_filter` e
   `isep_student_access`. Se depende de `openeducat_core` a secas y el alumno se calcula en el
   propio ledger (`_compute_student_id` + `_search_student_id`). Menos acoplamiento por un
   campo de conveniencia.
2. **Ubicación del motor de backfill.** El plan lo ponía en `irg.stripe.payment`; está en un
   AbstractModel propio, `irg.stripe.backfill`, para no engordar el modelo del ledger. El cron
   cuelga de `irg.stripe.payment` porque `ir.cron.model_id` necesita un modelo con tabla.
3. **`student_id` sí es filtrable.** El plan lo daba por no filtrable; tiene método `search`,
   así que sí lo es. Sigue sin ser agrupable ni ordenable, por lo que tree y pivot agrupan por
   `partner_id`.
4. **Fase 6 (metadata saliente) no implementada.** Es opcional en el plan y no hace falta para
   el listado. Queda pendiente.

## Bug encontrado y corregido durante la implementación

`_resolve_partner` y `_irg_identify_payment` encolaban **ambos** la misma incidencia, lo que
inflaba `occurrence_count` a 2 por un solo evento. Resuelto con el parámetro
`log_issues=False`: quien llama decide, y `_find_partner` (que no tiene llamante que encole)
conserva el comportamiento por defecto. Cubierto por `test_12_repeated_ambiguity_bumps_occurrence`.

## Error de instalación corregido

`views/res_partner_views.xml`: `partner_state` se usaba en `decoration-warning` sin estar
declarado como campo del tree embebido. Odoo lo rechaza en la validación de vistas.
