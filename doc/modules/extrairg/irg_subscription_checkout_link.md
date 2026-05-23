# irg_subscription_checkout_link

**Categoria:** Sales/Subscriptions  
**Version:** 16.0.1.0.0  
**Licencia:** LGPL-3  
**Instalable:** Si  
**Autor:** Instituto Raimon Gaja  
**Depende de:** `sale_subscription`, `isep_sale_subscription_extension`, `irg_sale_manual_confirmation_wizard`, `irg_payment_stripe_recurring`, `website`, `payment`

## Proposito

Permite enviar al alumno un enlace publico de checkout para preparar una suscripcion antes de que el asesor confirme manualmente el pedido.

El enlace no sustituye el proceso interno de admision. En `initial_payment` recoge un pago inicial y deja la confirmacion pendiente; en `setup_only` usa Stripe mediante `SetupIntent` o validacion para tokenizar la tarjeta sin crear la suscripcion Stripe de inmediato. En ambos casos el resultado queda pendiente en el pedido hasta que el wizard manual lo consume.

## Flujo de negocio

1. El asesor crea o revisa un presupuesto de suscripcion.
2. En la pestana **Checkout suscripcion**, genera el enlace publico y opcionalmente lo envia por email.
3. El alumno abre el enlace y completa el pago inicial o guarda la tarjeta, segun el modo efectivo calculado.
4. Odoo registra una transaccion/token Stripe pendiente en el pedido y bloquea nuevos usos del enlace.
5. El asesor revisa el pedido y ejecuta la confirmacion manual habitual.
6. Al confirmar, el wizard consume el token/transaccion pendiente, asigna `payment_token_id`, vincula la transaccion al pedido y, si aplica, crea la suscripcion nativa en Stripe.

## Acciones del asesor

En `sale.order`, la pestana **Checkout suscripcion** muestra:

| Campo/accion | Uso |
| --- | --- |
| `irg_subscription_checkout_mode` | Fuerza el modo del enlace o deja que Odoo lo calcule en `auto`. |
| `irg_subscription_checkout_effective_mode` | Modo final usado por el checkout: `initial_payment` o `setup_only`. |
| `irg_checkout_state` | Estado operativo del enlace y del resultado pendiente. |
| `irg_subscription_checkout_token` | Token privado del enlace. Se muestra oculto en formulario. |
| `irg_subscription_checkout_url` | URL publica que se envia al alumno. |
| `irg_pending_payment_transaction_id` | Transaccion Stripe pendiente de consumir por el wizard. |
| `irg_pending_payment_token_id` | Token Stripe pendiente de asignar al pedido. |
| **Generar enlace** | Crea el token si no existe y pasa el estado de `draft` a `sent`. |
| **Enviar enlace** | Genera el enlace y envia la plantilla `IRG Subscription Checkout Link`. |

Estados relevantes de `irg_checkout_state`:

| Estado | Significado |
| --- | --- |
| `draft` | Enlace no enviado o aun reutilizable si no hay pendiente. |
| `sent` | Enlace generado/enviado y pendiente de uso. |
| `paid_pending_confirmation` | Pago inicial recibido y pendiente de confirmacion manual. |
| `tokenized_pending_confirmation` | Tarjeta tokenizada y pendiente de confirmacion manual, sin suscripcion Stripe creada todavia. |
| `consumed` | El wizard manual ya consumio el pendiente. |
| `expired` | Reservado para caducidad operativa/manual. |
| `error` | Fallo al crear la suscripcion Stripe durante el consumo. |

## Comportamiento del enlace publico

Ruta publica:

```text
/irg/subscription/checkout/<sale_order_id>/<token>
```

La pagina muestra el pedido, el alumno y una caja de pago basada en `payment.checkout`. Solo se ofrecen proveedores Stripe compatibles con tokenizacion forzada.

El enlace es valido solo si:

- el token coincide con `irg_subscription_checkout_token`;
- el estado del checkout esta en `draft` o `sent`;
- el pedido esta en `draft`, `sent`, `sale` o `done`;
- no existe ya una transaccion o token pendiente en el pedido.

Si el enlace no es valido, el controlador devuelve `404`. Despues de registrar un pendiente, el enlace queda invalidado para evitar dobles capturas o doble tokenizacion.

Cuando el flujo llega a `setup_only`, el comportamiento esperado es tokenizar la tarjeta con la validacion de Stripe, guardar `irg_pending_payment_token_id` y dejar `irg_checkout_state` en `tokenized_pending_confirmation`. En ese modo no se crea una suscripcion Stripe en el callback publico.

## `initial_payment` vs `setup_only`

| Modo | Cuando se usa | Resultado esperado |
| --- | --- | --- |
| `initial_payment` | Cuando el primer vencimiento es hoy o anterior, o cuando el asesor lo fuerza. | Crea una transaccion de pago por el importe del primer plazo y solicita tokenizacion. |
| `setup_only` | Cuando el primer vencimiento es futuro, o cuando el asesor lo fuerza. | Crea una transaccion de validacion para guardar tarjeta sin cobrar importe inicial. |
| `auto` | Valor por defecto. | Calcula `initial_payment` si la primera fecha de vencimiento es menor o igual a hoy; en caso contrario calcula `setup_only`. |

El importe y fecha del primer plazo se obtienen de `subscription_schedule` cuando existe. Si no hay calendario, se calculan desde condiciones de pago o, como respaldo, desde `amount_total` y `start_date`/`date_order`.

## Consumo por wizard manual

El modulo hereda `irg.manual.confirmation.wizard.action_confirm()`. Tras la confirmacion normal del pedido, ejecuta `_irg_consume_pending_subscription_checkout()`.

Durante el consumo:

- si existe `irg_pending_payment_token_id` y el pedido no tiene `payment_token_id`, se asigna como token de pago de la suscripcion;
- si existe `irg_pending_payment_transaction_id`, se vincula la transaccion al pedido;
- si el pedido esta en `sale` o `done`, el modo Stripe es `stripe_subscription_real` o `payment_link_fallback`, y aun no existe una suscripcion `sub_...`, se llama a `_irg_create_stripe_subscription()`;
- si la creacion Stripe falla, el estado pasa a `error` y se registra excepcion en logs;
- si habia un pendiente y el proceso termina correctamente, el estado pasa a `consumed`.

El callback del checkout no confirma el pedido ni crea la suscripcion Stripe por si solo. Esa separacion mantiene la revision manual de admision como punto de control obligatorio.

Si el token pendiente ya puede consumirse y aplican las reglas de `irg_payment_stripe_recurring`, el wizard crea o reintenta la suscripcion Stripe en ese momento. Si la suscripcion ya existe (`sub_...`), no se duplica.

## Callback del checkout y reintentos

El callback interno `_irg_checkout_assign_token_callback` devuelve el resultado real de `_irg_record_checkout_transaction(tx)`. Si el registro de la transaccion se rechaza, Odoo no marca `callback_is_done` y el flujo puede reintentarse de forma segura.

Cuando el registro se rechaza, el sistema registra una advertencia con el token enmascarado para facilitar trazabilidad sin exponer credenciales ni identificadores completos.

## Restricciones Stripe e invariantes de seguridad

El modulo acepta una transaccion de checkout solo si cumple todas estas condiciones:

- `renewal_allowed` es verdadero;
- el partner comercial de la transaccion coincide con el partner comercial del pedido;
- la compania de la transaccion/token coincide con la del pedido cuando esta informada;
- no hay ya otro token o transaccion pendiente en el pedido;
- la transaccion y el token pertenecen a Stripe (`provider_code == "stripe"` y proveedor del token Stripe);
- el token tiene `stripe_payment_method`;
- el token pertenece al mismo partner comercial que el pedido;
- el proveedor del token coincide con el proveedor de la transaccion;
- en `initial_payment`, el importe de la transaccion coincide con el primer plazo con tolerancia menor a `0.01`;
- en `setup_only`, la transaccion debe ser de operacion `validation`.

El endpoint JSON elimina `custom_create_values` recibido desde el cliente y define internamente el callback permitido. Tambien fuerza `partner_id` al partner del pedido y rechaza proveedores que no esten en la lista compatible para ese pedido.

## Configuracion

Requisitos operativos:

- `web.base.url` debe apuntar al dominio publico correcto, porque se usa para construir `irg_subscription_checkout_url`.
- Debe existir un proveedor Stripe configurado en Odoo y compatible con tokenizacion.
- El partner del alumno debe poder pagar en la compania del pedido; si no, no se mostraran metodos de pago.
- El pedido debe tener datos de suscripcion coherentes: calendario de pagos, condiciones de pago, moneda, compania y partner.
- Para crear suscripciones nativas al consumir el pendiente, el puente de `irg_payment_stripe_recurring` debe estar correctamente configurado.

Plantilla de correo:

- XML ID: `irg_subscription_checkout_link.mail_template_subscription_checkout_link`
- Asunto: `Enlace de pago - {{ object.name }}`
- Destinatario: `object.partner_id.email`

## Pruebas ejecutadas

Suite automatizada del modulo:

```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf \
    -d test_irg_db -u irg_subscription_checkout_link \
    --test-enable --test-tags /irg_subscription_checkout_link \
    --stop-after-init
```

Resultado local: `16` tests OK en el modulo.

Suite combinada con `irg_payment_stripe_recurring`:

Resultado local: `24` tests OK.

Cobertura declarada por la suite:

- generacion de token y URL publica;
- rechazo de token invalido;
- calculo automatico de `setup_only` para vencimiento futuro;
- calculo automatico de `initial_payment` para vencimiento actual o pasado;
- tokenizacion sin suscripcion inmediata en `setup_only`;
- callback sin confirmacion automatica del pedido;
- registro de token pendiente y estado `tokenized_pending_confirmation`;
- retorno real del callback de asignacion de token y reintento cuando el registro es rechazado;
- rechazo de transacciones no finalizadas o sin `stripe_payment_method`;
- invalidacion del enlace tras registrar un pendiente;
- no consumo ni creacion Stripe desde callback sobre pedido confirmado;
- consumo posterior del token/transaccion por el wizard manual;
- omision de creacion Stripe si ya existe `stripe_subscription_id`;
- idempotencia al consumir pendientes y crear suscripcion Stripe una sola vez.

## Limitaciones y notas operativas

- No implementa una caducidad automatica del token; el estado `expired` existe como estado operativo.
- No permite elegir otros proveedores de pago: el flujo esta restringido a Stripe.
- El enlace publico no autentica al alumno; la seguridad depende del token largo, la validacion de pedido y las restricciones de partner/proveedor.
- Un pedido con token o transaccion pendiente no acepta nuevos usos del enlace hasta que el equipo gestione el pendiente.
- El modulo no sustituye la revision comercial/admisiones: la confirmacion manual sigue siendo obligatoria.
- En caso de estado `error`, revisar logs de Odoo y el estado del pedido en Stripe antes de reintentar operaciones.

## Changelog

- **2026-05-22:** creado el modulo `irg_subscription_checkout_link` para generar enlaces publicos de alta/pago de suscripcion antes del wizard manual, con captura Stripe pendiente, consumo posterior por admision manual, controles anti-doble cobro e invariantes de proveedor/token Stripe.
- **2026-05-23:** actualizado el comportamiento de `setup_only` para reflejar tokenizacion con `SetupIntent`/validacion sin creacion inmediata de suscripcion Stripe, con estado `tokenized_pending_confirmation` y consumo posterior por el wizard.
- **2026-05-23:** documentado el bugfix del callback: `_irg_checkout_assign_token_callback` devuelve el resultado real de `_irg_record_checkout_transaction(tx)`, permite reintento si el registro se rechaza y emite aviso con token enmascarado.
- **2026-05-23:** registrados los resultados de validacion del modulo individual y de la combinacion con `irg_payment_stripe_recurring`.
