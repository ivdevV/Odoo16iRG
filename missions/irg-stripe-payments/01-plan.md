# Módulo nuevo `irg_stripe_payments` — listado de pagos por usuario, conectado a Stripe

## Contexto

Hace falta ver, por contacto/alumno, todos los pagos que esa persona ha hecho en Stripe. Hoy eso no
existe: la investigación del repo muestra que la integración Stripe cubre bien las **suscripciones**,
pero deja tres agujeros que impiden justamente ese listado.

1. **Los pagos sueltos se descartan en silencio.** `_sync_payment_intent_succeeded`
   ([stripe_sync.py:590-602](addons-extra/extrairg/irg_stripe_subscriptions/models/stripe_sync.py:590))
   sale por `return` cuando el PaymentIntent no lleva `invoice` de Stripe. Es decir: Payment Links de
   pago único, cobros creados desde el Dashboard, Checkout puntual y Terminal no dejan rastro en
   Odoo. **No existe ningún modelo local de charges/payment intents** — no hay nada que listar.
2. **El matching por email puede vincular al contacto equivocado.**
   [stripe_sync.py:188-192](addons-extra/extrairg/irg_stripe_subscriptions/models/stripe_sync.py:152)
   hace `search([('email','=ilike',email.strip())], limit=1)` y acto seguido **escribe**
   `irg_stripe_customer_id` sobre el primero que salga: sin filtro de `active`/`type`/company, sin
   detectar ambigüedad. `res.partner.email` no tiene constraint de unicidad en ninguna parte
   (verificado por grep) y los duplicados son un problema real y conocido aquí — existen
   `irg_partner_safe_merge` e `irg_crm_lead_dedup` precisamente por eso. Un listado "por usuario"
   construido sobre esto muestra pagos ajenos.
   Bug adyacente: ese `write` es incondicional, así que **sobrescribe un `irg_stripe_customer_id`
   distinto ya existente** (líneas 178 y 191).
3. **No hay backfill.** Los pagos históricos de Stripe nunca se han traído. Un listado que empieza
   hoy sirve de poco.

Resultado buscado: un módulo instalable que mantiene un **ledger local de pagos Stripe**, lo vincula
al `res.partner` correcto (o lo manda a revisión manual, nunca adivina), y lo muestra en la ficha del
contacto, en la del alumno y en un menú propio con filtros.

**Decisiones cerradas:** todo va en un módulo nuevo, cero cambios en módulos existentes. Solo
backoffice interno — nada de portal del alumno en este alcance. El ancla de identidad es
`res.partner`; desde él se alcanza `op.student`, `res.users`, `sale.order` y `account.move`.

## Piezas existentes que se reutilizan (no se reinventan)

Núcleo Odoo NO está en el repo (imagen `odoo:16.0`); addons en `/mnt/extra-addons`, `addons_path` en
[odoo.local.conf:12](etc/odoo/odoo.local.conf:12). `extrairg` está en el path; `addons_irg` y
`migrationto16` **no** — el módulo nuevo va en `addons-extra/extrairg/`.

- **La columna de unión ya existe**: `res.partner.irg_stripe_customer_id`
  ([res_partner.py:12](addons-extra/extrairg/irg_payment_stripe_recurring/models/res_partner.py:12))
  + alias `stripe_customer_id` (related, store, index)
  ([res_partner.py:8-15](addons-extra/extrairg/irg_stripe_subscriptions/models/res_partner.py:8)).
- `_irg_ensure_stripe_customer()` ya crea el Customer con `metadata[odoo_partner_id]`
  ([res_partner.py:18-69](addons-extra/extrairg/irg_payment_stripe_recurring/models/res_partner.py:18)).
  **Ese metadata es el vínculo más fuerte disponible.**
- **Webhook con firma e idempotencia ya montado**: `/stripe/webhook`
  ([main.py:55](addons-extra/extrairg/irg_stripe_subscriptions/controllers/main.py:55)) — HMAC-SHA256
  propio (la lib `stripe` no está instalada, por diseño) + `stripe.event.log` con `event_id` único.
  Extender `stripe.sync.dispatch_event` da ambas cosas gratis. **No crear un tercer endpoint.**
- **`stripe.sync` ya se extiende desde otro módulo**:
  [irg_campus_certificates_portal/models/stripe_sync.py](addons-extra/extrairg/irg_campus_certificates_portal/models/stripe_sync.py)
  hace `_inherit = 'stripe.sync'` y llama a `super()`. Precedente exacto del patrón que usaremos.
- `payment.provider._stripe_make_request(endpoint, payload=..., method=...)` es el helper de bajo
  nivel. Idiom de lookup repetido 6 veces:
  `search([('code','=','stripe'),('state','in',('enabled','test'))], limit=1)`.
- `_amount_from_stripe_minor_units` ya existe y usa `currency.decimal_places`
  ([stripe_sync.py:93-98](addons-extra/extrairg/irg_stripe_subscriptions/models/stripe_sync.py:93)).
  Reutilizar; no meter un tercer `/100.0` hardcodeado.
- **Patrón de resolución por email a copiar**: `_resolve_partner_by_email` en
  [scholarship_webhook_service.py:134-163](addons-extra/extrairg/irg_student_scholarship_webhook/models/scholarship_webhook_service.py:134)
  — busca `op.student` por `partner_id.email`, devuelve `'ambiguous_email'` si `len > 1` en vez de
  coger `limit=1`.
- `op.student` hace `_inherits = {'res.partner': 'partner_id'}`, así que `student.email` **es**
  `res.partner.email`. Desde partner: `partner.user_ids` (portal), `partner.student_id`
  ([irg_partner_openeducat_info/models/res_partner.py:8-13](addons-extra/extrairg/irg_partner_openeducat_info/models/res_partner.py:8), compute **no almacenado**).
- `payment.transaction.partner_id` es la fuente de partner de máxima confianza para cualquier pago que
  pasó por el checkout del portal. Hoy nadie la explota.

## Estructura del módulo

```
addons-extra/extrairg/irg_stripe_payments/
├── __init__.py
├── __manifest__.py                    depends: ['irg_stripe_subscriptions',
│                                                'irg_partner_openeducat_info', 'account']
├── README.md
├── data/
│   ├── ir_config_parameter_data.xml   email_match_mode, backfill_max_days
│   └── ir_cron_data.xml               cron de backfill (active=False)
├── models/
│   ├── irg_stripe_payment.py          el ledger
│   ├── irg_stripe_identity_review.py  cola de revisión
│   ├── stripe_sync.py                 _inherit='stripe.sync': eventos + resolución endurecida
│   ├── res_partner.py                 O2M + contadores + acción "ver pagos"
│   └── op_student.py                  stat button
├── wizard/
│   ├── irg_stripe_backfill_wizard.py
│   └── irg_stripe_identity_link_wizard.py
├── security/ir.model.access.csv
├── views/
│   ├── irg_stripe_payment_views.xml
│   ├── irg_stripe_identity_review_views.xml
│   ├── res_partner_views.xml
│   ├── op_student_views.xml
│   └── menus.xml
└── tests/
    ├── __init__.py
    ├── test_partner_resolution.py
    ├── test_one_off_payment_sync.py
    ├── test_backfill.py
    └── test_security.py
```

### Invariante que hace imposible el doble conteo

> `irg.stripe.payment` es un **ledger de solo lectura**. Nunca escribe `sale.note.inv.legacy`, nunca
> toca `sale.subscription.schedule`, nunca crea `account.move` ni `account.payment`, nunca muta
> campos de dinero de `sale.order`. La conciliación monetaria sigue siendo exclusiva de
> `_sync_invoice_paid` / `_register_paid_invoice_on_schedule` del módulo base.

Va en el docstring del módulo y está cubierta por test.

## Fase 0 — Recon (solo lectura, bloquea el resto)

**T0.1 — Verificar el contrato de transporte de Stripe.** Leer `payment_stripe/models/payment_provider.py`
y `const.py` dentro del contenedor; hacer un `GET charges?limit=1` real en modo test.
*Acepta:* documentado en `execution.md`: (a) header `Stripe-Version` fijado; (b) confirmado que los
query params van **en el string del endpoint** y que `payload` en GET se ignora (`_stripe_make_request`
manda `payload` como `data=`, o sea body — ninguna llamada del repo pagina hoy, es terreno no probado);
(c) confirmado que 4xx —incluido 429— lanza `ValidationError` en vez de devolver `{'error': ...}`
(todos los `if not res.get('error')` del repo son medio código muerto); (d) si el PaymentIntent trae
`charges.data` o `latest_charge`.

**T0.2 — Medir la población de emails duplicados.** SQL de solo lectura: partners activos no
fusionados que comparten email. *Acepta:* un número. Si sale alto (> ~500), el backfill arranca con
`email_match_mode=disabled` y se apoya solo en metadata/customer id.

**T0.3 — Enumerar la config de webhooks en el Dashboard de Stripe.** Qué eventos están suscritos en
`/stripe/webhook` vs `/payment/stripe/webhook`, en test y en live. *Acepta:* tabla en `execution.md`.
**Si `payment_intent.succeeded` no llega hoy a `/stripe/webhook`, nada de la Fase 2 se dispara hasta
cambiar el Dashboard** — es un paso de despliegue, no de código, y debe quedar escrito.

## Fase 1 — El ledger y la cola de revisión

**T1.1 — Scaffold del módulo.** Manifest, `__init__`, ACLs vacías, README con la invariante.
*Acepta:* `-i irg_stripe_payments` instala limpio en DB scratch, sin warnings de ACL en el log.

**T1.2 — Modelo `irg.stripe.payment`** (prefijo `irg.` por convención del repo: `irg.certificate.request`,
`irg.partner.safe.merge.audit`) + `_upsert_from_stripe`.

| Campo | Tipo | Nota |
|---|---|---|
| `stripe_id` | Char required index, `unique` | **Ancla de idempotencia**: `pi_...` si hay PaymentIntent, si no `ch_...` |
| `stripe_payment_intent_id` / `stripe_charge_id` / `stripe_checkout_session_id` / `stripe_invoice_id` / `stripe_customer_id` | Char index | |
| `stripe_customer_email` | Char | de `billing_details.email` / `receipt_email` / `customer_details.email` |
| `partner_id` | M2o `res.partner` index `ondelete='restrict'` | **la columna del listado** |
| `partner_state` | Selection `linked` / `review` / `unlinked` | estado de identidad |
| `partner_match_method` | Selection `payment_transaction` / `client_reference_id` / `object_metadata` / `stripe_customer_id` / `customer_metadata` / `email_unique` / `student_email_unique` / `manual` | auditoría de **cómo** se decidió |
| `state` | Selection `succeeded` / `failed` / `canceled` / `refunded` / `partially_refunded` | estado de dinero, distinto del de identidad |
| `amount`, `amount_refunded` | Monetary | vía `_amount_from_stripe_minor_units`, nunca `/100` |
| `currency_id` | M2o `res.currency` | + `stripe_currency` Char crudo, por si la divisa no existe en Odoo |
| `payment_date` | Datetime | de `created` |
| `description`, `receipt_url`, `hosted_invoice_url` | Char | el `receipt_url` es lo que soporte necesita enseñar |
| `sale_order_id` / `move_id` / `payment_transaction_id` / `stripe_subscription_id` | M2o `ondelete='set null'` | |
| `is_subscription_payment` | Boolean stored | `bool(stripe_invoice_id)` |
| `student_id` | related `partner_id.student_id` readonly | **no almacenado** (el compute origen no lo es) → solo formulario; en tree/pivot agrupar por `partner_id` |
| `origin` | Selection `webhook` / `backfill` / `manual` | |
| `review_id`, `company_id`, `raw_payload` | | `raw_payload` Text con widget `ace`, como `stripe.subscription.raw_payload` |

`_order = 'payment_date desc, id desc'`.
Semántica de upsert: **merge, no clobber** — nunca sobrescribir un campo no vacío con uno vacío,
nunca bajar la confianza de `partner_match_method` una vez fijada.
*Acepta:* upsert dos veces (payload parcial, luego completo) → una fila, ningún campo regresado a
vacío; importe en JPY correcto (0 decimales); el constraint único salta ante duplicado forzado.

**T1.3 — Modelo `irg.stripe.identity.review`** + `irg.stripe.identity.link.wizard`.

Modelo aparte, no un simple `partner_state='review'`, porque la ambigüedad también ocurre en
`customer.subscription.*` y `checkout.session.completed`, donde no hay fila de pago one-off — y ese es
justamente el caso que hoy adivina en silencio.

Campos: `name` computed (`"cus_xxx · ana@x.com · 2 candidatos"`), `reason` (`ambiguous_email` /
`not_found` / `conflicting_customer_id` / `metadata_partner_missing`), `stripe_object_type`,
`stripe_object_id` index, `stripe_customer_id`, `stripe_email`, `candidate_partner_ids` M2M (entre lo
que nos negamos a elegir), `partner_id` (decisión humana), `state` `open`/`resolved`/`ignored`,
`resolution_note` (requerido si `ignored`), `resolved_by_id`, `resolved_at`, `occurrence_count`,
`last_seen_at`, `payment_ids` O2M.

Dedup: `search([('stripe_object_id','=',oid),('reason','=',r),('state','=','open')], limit=1)` → sube
`occurrence_count`, no crea fila nueva.
*Acepta:* una ambigüedad crea exactamente una fila abierta; la segunda idéntica sube el contador a 2;
vincular escribe el partner en todos los `irg.stripe.payment` relacionados, respeta la guarda de
conflicto y marca `partner_match_method='manual'`.

## Fase 2 — Conexión con Stripe: eventos entrantes

Todo en `irg_stripe_payments/models/stripe_sync.py` con `_inherit = 'stripe.sync'`, llamando a
`super()`. Cero ficheros tocados fuera del módulo.

| Evento | Acción |
|---|---|
| `payment_intent.succeeded` | **El agujero principal.** Siempre upsert de `irg.stripe.payment`; *después* `super()`, que mantiene la delegación a `_sync_invoice_paid` cuando hay `invoice`. |
| `payment_intent.payment_failed` | Upsert con `state='failed'`. Da visibilidad a soporte cuando un alumno "dice que pagó". |
| `charge.refunded` | Actualizar `amount_refunded` y `state`. Los eventos de PaymentIntent **no** disparan en reembolso; sin esto el listado miente para siempre. |
| `checkout.session.completed` | Si `mode == 'payment'` y hay `payment_intent`, upsert arrastrando `client_reference_id`/`metadata` de la sesión (la señal de identidad más fuerte; el PI a menudo no lleva ninguna). |
| `charge.succeeded` | **No suscribir.** En un pago con tarjeta normal lleva `payment_intent` y es duplicado estricto del anterior; suscribir ambos dobla el volumen de webhook por cero información. Los charges sin PI (legacy, algunos Terminal) los recoge el backfill, que pagina `charges`. Si en producción resultan continuos, añadir el handler con guarda `if obj.get('payment_intent'): return`. |
| `charge.dispute.created` | Fuera de alcance (pregunta abierta). |

Matriz anti-doble-conteo:

| Colisión | Mecanismo |
|---|---|
| `payment_intent.succeeded` × `charge.succeeded` | No suscribir el segundo |
| `payment_intent.succeeded` × `checkout.session.completed` | Ambos pasan por un único `_upsert_stripe_payment(vals)` con clave `stripe_id` |
| `payment_intent.succeeded` × `invoice.paid` | Una sola fila de ledger; **la conciliación monetaria no se toca** — la triple guarda de `_sync_invoice_paid` ([stripe_sync.py:547-565](addons-extra/extrairg/irg_stripe_subscriptions/models/stripe_sync.py:547)) sigue siendo el único camino y el ledger no escribe en schedules |
| `/stripe/webhook` × `/payment/stripe/webhook` | El ledger **enlaza** a `payment.transaction` (`provider_reference == pi_id`), no la duplica |
| Backfill × webhook | Misma clave única + mismo upsert |
| Evento entregado dos veces | Ya resuelto por `stripe.event.log` |

**T2.1 (RED→GREEN)** — handler de `payment_intent.succeeded`. *Acepta:* el test "PI sin invoice crea
fila" pasa de rojo a verde; "PI con invoice produce exactamente un `sale.note.inv.legacy`" verde; los
10 tests de `irg_stripe_subscriptions/tests/test_stripe_subscriptions.py` siguen verdes **sin tocar**
(en especial `test_10`, el de dedup).
**T2.2** — `charge.refunded` + `payment_intent.payment_failed`. *Acepta:* el reembolso actualiza la
fila existente sin crear una segunda; un reembolso de charge desconocido crea fila en `review`, no
excepción.
**T2.3** — `checkout.session.completed` para `mode='payment'`. **Riesgo de orden de MRO**: el override
de `irg_campus_certificates_portal` hace `return` temprano para `cert_req_*`, así que si corre primero
el ledger nunca se crea. Mitigación: el upsert va **antes** del `super()`, con test explícito en ambos
órdenes de instalación. *Acepta:* una sesión de certificado sigue llegando a
`_process_stripe_checkout_payment` **y además** genera fila de ledger con el mismo partner.
**T2.4** — enlace con `payment.transaction`: buscar `provider_reference == pi_id`; si hay, tomar
`tx.partner_id`, `tx.sale_order_ids[:1]`, `tx.invoice_ids[:1]`. *Acepta:* el módulo nunca crea un
`payment.transaction` (contador invariante).

## Fase 3 — Resolución de identidad endurecida (dentro del módulo nuevo)

`_inherit = 'stripe.sync'` sobrescribiendo `_find_partner` con firma **byte-idéntica**, más un método
rico nuevo. Los 4 call sites del módulo base quedan intactos y se benefician del arreglo.

```
_resolve_partner(customer_id=False, email=False, allow_email_fallback=True,
                 source=None, source_ref=None)
    -> {'partner': <res.partner, 0 o 1>,
        'status': 'matched'|'ambiguous_email'|'not_found'|'no_input'|'conflicting_customer_id',
        'method': 'stripe_customer_id'|'customer_metadata'|'email_unique'|'student_email_unique'|False,
        'candidates': <recordset>, 'email': <str normalizado|False>}

_find_partner(customer_id, email=False) -> self._resolve_partner(customer_id, email)['partner']
```

Escalera:

0. Pistas explícitas del llamante (`client_reference_id` `odoo_order_<id>` / `odoo_partner_<id>`,
   `metadata.odoo_order_id` / `odoo_partner_id`) — el módulo base ya las parsea en
   [_sync_checkout_session:379-402](addons-extra/extrairg/irg_stripe_subscriptions/models/stripe_sync.py:361).
1. `stripe_customer_id` / `irg_stripe_customer_id`. **Si `len > 1` → `conflicting_customer_id`, vacío + cola** (hoy: `limit=1` silencioso).
2. `GET customers/{cid}` → `metadata.odoo_partner_id` → `browse().exists()`. Si está archivado o
   fusionado → cola, no match. Cosechar `res['email']` como fallback.
3. Email, solo si `allow_email_fallback` y `email_match_mode != 'disabled'`:

```python
normalized = (email or '').strip().lower()
if not normalized or '@' not in normalized: return not_found

extra = []
if 'irg_merged_into_partner_id' in env['res.partner']._fields:   # tombstone de irg_partner_safe_merge
    extra = [('irg_merged_into_partner_id', '=', False)]

# Tier A — alumnos primero (patrón de irg_student_scholarship_webhook)
students = env['op.student'].sudo().search([('partner_id.email','=ilike',normalized)] + <extra prefijado>)
if len(students) == 1: -> matched, method='student_email_unique'
if len(students) > 1:  -> ambiguous_email, candidates=students.partner_id     # STOP. sin limit=1

# Tier B — contactos (active_test ON excluye archivados)
cands = env['res.partner'].sudo().search([('email','=ilike',normalized)] + extra)
n = cands.filtered(lambda p: p.type == 'contact') or cands      # descarta direcciones hijas
n = n.filtered(lambda p: not p.is_company)       or n           # prioriza persona sobre empresa
len(n) == 1 -> matched/'email_unique';  len(n) > 1 -> ambiguous_email;  else not_found
```

Guarda de escritura (arregla el segundo bug):

```python
existing = partner.irg_stripe_customer_id
if existing and existing != customer_id:      # NO escribir
    -> cola, reason='conflicting_customer_id'
elif not existing and status == 'matched':
    partner.write({'irg_stripe_customer_id': customer_id})
```

Kill switch por `ir.config_parameter` `irg_stripe.email_match_mode` ∈ `strict_unique` (default) |
`disabled` | `legacy` (restaura el `limit=1` sin redeploy).

**Compatibilidad verificada** leyendo los consumidores del módulo base: `_sync_subscription_object:207,249-252`
usa `partner.id if partner else False`; `_sync_checkout_session:405-410` accede a
`partner.stripe_customer_id` sobre recordset vacío → `False`. Ambos seguros. El único cambio de
comportamiento —vacío en vez de adivinar— es el arreglo buscado y va al changelog: podrán crearse
`stripe.subscription` con `partner_id = False`, visible en UI.

**T3.1 (RED)** — tests de resolución; los de ambigüedad y conflicto fallan con el comportamiento actual.
**T3.2 (GREEN)** — implementar `_resolve_partner` + wrapper + guarda + parámetros de config.
*Acepta:* nuevos tests verdes; los 10 preexistentes verdes sin modificar.

## Fase 4 — Backfill histórico (lo que llena el listado hacia atrás)

**Paginar `charges`, no `payment_intents`:**

| | `charges` | `payment_intents` |
|---|---|---|
| Cubre charges legacy/Terminal sin PI | sí | no (invisibles) |
| Trae `amount_refunded` / `refunded` | sí | no (segunda llamada) |
| Trae `invoice`, `customer`, `billing_details.email` | sí | parcial |
| Riesgo de duplicado | un PI puede tener varios charges tras reintentos | ninguno |

El duplicado se neutraliza con la clave `charge.payment_intent or charge.id`. Modo alternativo
`payment_intents` en el wizard para cuentas sin charges legacy.

Paginación — **el query string va en el endpoint, no en `payload`**:

```python
endpoint = f"charges?limit={page_size}&created[gte]={ts_from}&created[lte]={ts_to}"
if cursor:
    endpoint += f"&starting_after={cursor}"
res = provider._stripe_make_request(endpoint, method='GET')
cursor, more = res['data'][-1]['id'], res.get('has_more')
```

Resiliencia: `_stripe_make_request` **lanza `ValidationError` en 4xx incluido 429**, no devuelve
`{'error': ...}`. Cada página en try/except, backoff 0.5→2→8s (máx. 3 intentos), `sleep(0.2)` entre
páginas correctas; al fallar en firme, persistir cursor, marcar `partial` y salir limpio — nunca
propagar la excepción fuera del cron.

Idempotencia: `ir.config_parameter` `irg_stripe.backfill_cursor` / `_window_from` / `_window_to` /
`_done_until`; upsert merge-not-clobber; commit cada 5 páginas **solo en el cron** (guardado para que
tests y wizard corran en una transacción).

Guardas: ventana obligatoria, máx. 92 días (`irg_stripe.backfill_max_days`), `provider_id`
**explícito** (no confiar en `search(..., limit=1)`, ver riesgo 8) y **dry-run** que cuenta y
previsualiza sin escribir.

**T4.1** — motor `_run_backfill`. *Acepta:* el test asserta el literal `starting_after=` **en el
argumento del endpoint** (no solo el resultado); re-ejecutar el mismo rango → 0 creados y campos de
dinero idénticos; `ValidationError` en la página 2 → `partial` + cursor persistido + segunda ejecución
completa.
**T4.2** — `irg.stripe.backfill.wizard` (TransientModel): `provider_id`, `date_from`, `date_to`,
`mode`, `dry_run`, campo de resumen. *Acepta:* ventana > 92 días → `UserError`; dry-run escribe cero
filas; corrida real de 7 días en test coincide con el export del Dashboard.
**T4.3** — cron resumible, `active=False` por defecto (convención de
`irg_payment_stripe_recurring/data/cron_data.xml`). *Acepta:* matar el proceso a media ejecución y
relanzar reanuda desde el cursor sin duplicados.

## Fase 5 — El listado (el entregable visible)

**T5.1 — Vistas del ledger.** Tree con `payment_date`, `partner_id`, `amount`, `state`,
`partner_match_method`, `receipt_url`; form con el `raw_payload` en una página técnica; pivot y graph.
Search view con filtros **Sin vincular** (`partner_state='unlinked'`), **En revisión**,
**Reembolsados**, **Solo suscripción** / **Solo pagos sueltos**, y group by partner / mes / método de
match / estado.

**T5.2 — Ficha del contacto.** Heredar `irg_stripe_subscriptions.view_partner_form_inherit_stripe`
(no `base.view_partner_form`, así el target del xpath está garantizado; precedente:
`irg_student_payment_status/views/op_student_views.xml` hereda de otro módulo iRG, no del base).
Dentro de la página *Stripe*: O2M `irg_stripe_payment_ids` + `stat_button` con contador y total
pagado. Campos computados no almacenados en `res.partner`: `irg_stripe_payment_count`,
`irg_stripe_paid_total`.

**T5.3 — Ficha del alumno.** Heredar `openeducat_core.view_op_student_form`, `oe_stat_button`
"Pagos Stripe" → act_window sobre `irg.stripe.payment` con `domain=[('partner_id','=',partner_id)]`
(`op.student` hace `_inherits` de `res.partner`, así que `partner_id` está en el registro).

**T5.4 — Menús** bajo `irg_stripe_subscriptions.menu_stripe_integration_root` ("Integración Stripe",
padre `sale.menu_sale_config`): *Pagos Stripe* y *Revisión de identidad* (filtro por defecto
`state='open'`, `decoration-danger="reason=='conflicting_customer_id'"`). Formulario de revisión con
los hechos de Stripe en solo lectura, `candidate_partner_ids` como lista readonly con enlaces, selector
`partner_id` y botones *Vincular* / *Ignorar* (este exige `resolution_note`).

*Acepta (T5.1-5.4):* ficha de contacto muestra los pagos; el stat button del alumno abre la lista
filtrada; ambos menús renderizan; sin errores de herencia de vistas al instalar ni al hacer `-u base`.

## Fase 6 (opcional) — Metadata saliente

Sube la tasa de match futura, pero no es imprescindible para el listado. Todo por herencia desde el
módulo nuevo, sin tocar ficheros ajenos:

- Override de `action_irg_create_stripe_payment_link`
  ([sale_order.py:306-318](addons-extra/extrairg/irg_stripe_subscriptions/models/sale_order.py:306))
  para añadir `metadata[odoo_partner_id]`, `metadata[odoo_partner_name]` y
  `subscription_data[metadata][odoo_partner_id]`. Hoy el código saliente **solo emite `odoo_order_`**,
  nunca `odoo_partner_`.
- `res.partner.action_irg_push_stripe_metadata()` + cron por lotes de 200 (`active=False`):
  `POST customers/{cid}` con `metadata[odoo_partner_id]`. El POST **fusiona** claves en Stripe, no las
  borra; verificar primero en un customer de test. Resumibilidad vía Boolean almacenado
  `res.partner.irg_stripe_metadata_synced` (barato, visible, reseteable) en vez de un cursor opaco.

*Acepta:* payload del payment link contiene `metadata[odoo_partner_id]` (test); el cron es no-op en la
segunda pasada; un customer de test conserva sus claves de metadata previas.

## Seguridad

`security/ir.model.access.csv`: los registros son generados por máquina, así que **solo
`base.group_system` crea o borra**. `sales_team.group_sale_salesman` lee;
`account.group_account_invoice` lee + resuelve la cola. Wizard de backfill solo `base.group_system`
(quema cuota de API y escribe en masa). Ambos grupos ya se usan en otros ACL de `extrairg`, no se
introduce ninguno nuevo.

La acción de resolver revisión llama `check_access_rights('write')` + `check_access_rule('write')` en
servidor — la visibilidad del botón no es un control.

El webhook sigue `auth='public'` con HMAC; los eventos nuevos no añaden superficie de auth. Sin
manejo de secretos nuevo, sin `ir.config_parameter` que contenga secretos.

**Hallazgo aparte, NO se arregla aquí:** `irg_stripe_subscriptions/security/ir.model.access.csv` da
`base.group_user` CRUD completo sobre `stripe.subscription`, `stripe.payment.link` y
`stripe.event.log` — cualquier usuario interno puede borrar el log de idempotencia del webhook. Misión
separada; no copiar el patrón.

## Tests

Convención del repo: `tests/__init__.py`, `@tagged('post_install','-at_install')`, `TransactionCase`,
Stripe mockeado con `patch.object(type(provider), '_stripe_make_request', ...)` (patrón ya usado en
[test_stripe_subscriptions.py:504-556](addons-extra/extrairg/irg_stripe_subscriptions/tests/test_stripe_subscriptions.py)).

- **`test_partner_resolution.py`** — resolución por customer id / alias / metadata; **dos partners
  activos con el mismo email → recordset vacío, `status='ambiguous_email'`, exactamente una fila de
  revisión con 2 candidatos, y `irg_stripe_customer_id` NO escrito en ninguno de los dos**; archivado
  excluido; si uno es `op.student` gana el alumno; email que apunta a partner con otro customer id →
  sin escritura + `conflicting_customer_id`; el wrapper legacy devuelve recordset (no `None`);
  `email_match_mode='disabled'` salta el tier de email; ambigüedad repetida sube `occurrence_count`.
- **`test_one_off_payment_sync.py`** — PI sin invoice crea fila (el RED del agujero principal); mismo
  PI en dos eventos → una fila; sesión + PI → fila fusionada y el partner del `client_reference_id`
  gana; PI con invoice → `_sync_invoice_paid` sigue corriendo y hay **exactamente un**
  `sale.note.inv.legacy`; `charge.refunded`; irresoluble → `review`; PI que casa con
  `payment.transaction.provider_reference` → `partner_id == tx.partner_id`; JPY con `decimal_places`.
- **`test_backfill.py`** — paginación (assert sobre el string del endpoint), re-run idempotente,
  `ValidationError` a media página → `partial` + reanudación, ventana > 92 días, dos charges de un PI
  → una fila, charge sin PI, dry-run no escribe.
- **`test_security.py`** — `base.group_user` no puede crear (`AccessError`); la acción de vincular
  falla en servidor aunque se fuerce el botón.
- **Regresión obligatoria:** los 10 tests de `test_stripe_subscriptions.py` verdes **sin modificar**.

## Verificación end-to-end

Runtime `docker-compose.local.yml`, contenedor `odoo16irg_local`. Instalar y testear sobre DB scratch.

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d odoo16irg_test -i irg_stripe_payments --test-enable --stop-after-init --log-level=test
```

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d odoo16irg_test -u irg_stripe_subscriptions --test-enable --stop-after-init --log-level=test
```

```bash
stripe listen --forward-to http://localhost:8069/stripe/webhook --events payment_intent.succeeded,payment_intent.payment_failed,charge.refunded,checkout.session.completed
```

`stripe listen` imprime un `whsec_...` **nuevo**: hay que ponerlo en Ajustes → *Stripe Webhook Secret*
(`ir.config_parameter` `stripe.webhook_secret`) de la DB de test, o `_verify_stripe_signature`
([main.py:15-53](addons-extra/extrairg/irg_stripe_subscriptions/controllers/main.py:55)) rechaza todo
con 400.

| Escenario | Esperado |
|---|---|
| `stripe trigger payment_intent.succeeded` (customer desconocido) | una fila en el listado, `partner_state='review'`, una revisión abierta |
| Customer con `metadata[odoo_partner_id]=<id>` + PI confirmado | fila `linked`, `method='customer_metadata'`, aparece en la ficha del contacto y en el stat button del alumno |
| `stripe refunds create --charge ch_x` | misma fila, `amount_refunded` set, `state='refunded'` |
| **2 partners activos con el mismo email + PI sin metadata** | exactamente una revisión con 2 candidatos, y `SELECT irg_stripe_customer_id FROM res_partner WHERE id IN (a,b)` devuelve NULL en ambos |
| `stripe trigger invoice.payment_succeeded` sobre sub con orden | plazo marcado pagado **una sola vez**; conteo de `sale_note_inv_legacy` invariante al reenviar |
| Backfill 7 días, dry-run y real | conteo = export de Payments del Dashboard; dos corridas → mismo número de filas |

**Orden de despliegue:** instalar con `email_match_mode=strict_unique` → (si se hace la Fase 6) correr
el cron de push de metadata hasta el final → backfill de más antiguo a más nuevo en trozos mensuales
fuera de horario → vigilar el crecimiento de la cola de revisión; si se inunda, poner
`email_match_mode=disabled` durante el backfill y confiar solo en metadata/customer id.

## Riesgos

1. **Deriva de versión de API (el mayor).** `stripe.api_version` está en `res_config_settings.py:26` y
   **no lo lee nadie**; la versión real es la que fija `payment_stripe`. Peor: los payloads de webhook
   usan la versión del *endpoint* del Dashboard, que puede diferir de la de las llamadas API — el mismo
   PaymentIntent puede llegar con `charges.data[0]` por webhook y `latest_charge` por API. Mitigación:
   helpers agnósticos de forma (`_pi_charge_id`, `_pi_email`, `_pi_invoice_id`) que miren ambas, al
   estilo defensivo de `_extract_subscription_id_from_invoice`. T0.1 cierra antes de la Fase 2.
2. **4xx lanza, no devuelve.** El retry del backfill debe capturar `ValidationError`.
3. **Query params en GET sin precedente** en el repo. T0.1 lo verifica con una llamada real antes de
   escribir el bucle.
4. **Cambio de comportamiento deliberado**: `_find_partner` empezará a devolver vacío donde antes
   adivinaba. Visible en UI (subs sin partner) → línea explícita en el changelog.
5. **Orden de MRO en `_sync_checkout_session`** con `irg_campus_certificates_portal` (ver T2.3).
6. **Inundación de la cola en el backfill** si T0.2 sale alta → `email_match_mode=disabled` por defecto
   durante el backfill.
7. **`stripe.event.log` crece sin política de retención** y añadimos tipos de evento. Fuera de alcance, señalado.
8. **`_get_stripe_provider()` usa `limit=1`.** Con provider test y live activos a la vez, o dos cuentas
   Stripe, el backfill pagina la cuenta equivocada en silencio → `provider_id` explícito en el wizard.
9. **Divisa inexistente en Odoo** → `currency_id` vacío rompe el Monetary; por eso `stripe_currency`
   Char siempre poblado + fallback a la divisa de la compañía.
10. **`student_id` es compute no almacenado** → no filtrable ni agrupable; solo formulario. En tree y
    pivot se agrupa por `partner_id`.
11. **ACLs preexistentes demasiado amplias** en el módulo base (ver Seguridad). Señalado, no arreglado.
12. **Multi-compañía**: `company_id` está planificado, las record rules no. Si la DB es multi-compañía,
    son obligatorias antes de instalar.
13. **Desinstalar el módulo nuevo devuelve el bug de matching por email**, al vivir el fix aquí. Es la
    contrapartida aceptada de mantenerlo todo en un solo módulo; queda escrita en el README.

## Preguntas abiertas (no bloquean empezar por Fase 0/1)

- ¿Qué eventos están suscritos hoy en cada uno de los dos endpoints de webhook, en live y en test?
  Si `payment_intent.succeeded` no llega a `/stripe/webhook`, la Fase 2 no dispara hasta cambiar el Dashboard.
- ¿Hasta dónde atrás va el backfill y cuántos charges hay? Determina troceado y presupuesto de API.
- ¿`odoo16irg` es multi-compañía? Determina si las record rules son obligatorias.
- ¿Hay varias cuentas Stripe o una legacy? Determina si `provider_id` debe ser campo de primera clase
  en el ledger.
- ¿Se rastrean disputas/chargebacks (`charge.dispute.created`)? Ahora mismo fuera de alcance.
- Ante email ambiguo, ¿la cola debe notificar a alguien (actividad, mail a un alias de ops) o basta el menú?

## Flujo Git y SDD

Rama desde `Dev_iRG` (nunca desde `main`): `feat/irg-stripe-payments`. Misión SDD `full`, tier
`complex` (>5 ficheros, migración de datos históricos, resolución de identidad → firma del Security
Advisor obligatoria). Artefactos en `missions/irg-stripe-payments/`
(`01-plan.md`, `02-progress.md`, `02b-review.md`, `03-validation.md`, `artifacts/`) +
`CHANGELOG_<fecha>_irg_stripe_payments.md` en la raíz. Sin `PASS global` no se abre PR; el merge lo
hace el usuario.

Nota de conocimiento a dejar escrita, con los tres hallazgos no obvios: (a) los query params van en el
string del endpoint de `_stripe_make_request`, (b) `_stripe_make_request` lanza en 4xx, (c) la
invariante ledger-nunca-concilia.

## Fuentes web consultadas

- [Stripe — Odoo 16.0 documentation](https://www.odoo.com/documentation/16.0/applications/finance/payment_providers/stripe.html)
- [odoo/odoo 16.0 — payment_stripe](https://github.com/odoo/odoo/blob/16.0/addons/payment_stripe/models/payment_transaction.py)
- [Payment Link | Stripe API Reference](https://docs.stripe.com/api/payment_links/payment_links)
- [The Checkout Session object](https://docs.stripe.com/api/checkout/sessions/object)
- [Pass data through Stripe payment links](https://www.cjav.dev/articles/pass-data-through-stripe-payment-links)
