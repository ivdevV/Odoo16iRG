# 03 — Validación

Todo ejecutado en local sobre `docker-compose.local.yml`. BD `scratch_stripe_payments`, clon
de `test_irg_db`. Ni producción ni el servidor de beta se han tocado.

## Instalación

```
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d scratch_stripe_payments \
  -i irg_stripe_payments --stop-after-init --log-level=warn --no-http
```

Evidencia:

```
irg_payment_stripe_recurring = installed
irg_stripe_payments = installed
irg_stripe_subscriptions = installed
payment_stripe = installed
```

Sin errores. Los WARNING del log son preexistentes de otros módulos (`res.partner.gender`
sobrescribiendo selection, parámetros de campo desconocidos en `sale.order` y `op.batch`) y
aparecen igual sin este módulo.

**PASS** — el módulo instala limpio y arrastra correctamente su cadena de dependencias.

## Suite propia

```
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d scratch_stripe_payments \
  -u irg_stripe_payments --test-enable --test-tags /irg_stripe_payments \
  --stop-after-init --log-level=test --no-http
```

Evidencia (`artifacts/tests-irg_stripe_payments.txt`):

```
odoo.tests.stats: irg_stripe_payments: 52 tests 1.02s 2875 queries
odoo.tests.result: 0 failed, 0 error(s) of 44 tests
```

**PASS** — 44 tests, 0 fallos, 0 errores.

Cobertura por criterio de aceptación del plan:

| Criterio del plan | Test | Estado |
|---|---|---|
| PI sin invoice crea fila (el agujero principal) | `test_one_off_01` | PASS |
| Mismo PI dos veces → una fila | `test_one_off_02` | PASS |
| Sesión + PI → fila fusionada, gana el `client_reference_id` | `test_one_off_06` | PASS |
| PI con invoice → la conciliación se delega exactamente una vez | `test_one_off_07` | PASS |
| `charge.refunded` actualiza sin crear segunda fila | `test_one_off_08`, `_09` | PASS |
| Irresoluble → `review` | `test_one_off_03` | PASS |
| `payment.transaction` gana al email | `test_one_off_04` | PASS |
| Divisa de 0 decimales (JPY) | `test_one_off_11` | PASS |
| Forma `latest_charge` soportada | `test_one_off_13` | PASS |
| **Email ambiguo: no elige, encola, y no escribe en ninguno** | `test_resolution_03` | PASS |
| Archivado excluido | `test_resolution_04` | PASS |
| Alumno gana al contacto suelto | `test_resolution_05` | PASS |
| Customer ID distinto no se sobrescribe | `test_resolution_07` | PASS |
| `_find_partner` devuelve recordset, vacío ante ambigüedad | `test_resolution_09` | PASS |
| `email_match_mode` disabled / legacy | `test_resolution_10`, `_11` | PASS |
| Ambigüedad repetida sube `occurrence_count`, no duplica | `test_resolution_12` | PASS |
| Paginación: `starting_after` en el string del endpoint | `test_backfill_01` | PASS |
| Re-run idempotente | `test_backfill_02` | PASS |
| Dos charges de un PI colapsan | `test_backfill_03` | PASS |
| Charge sin PI se indexa por `ch_...` | `test_backfill_04` | PASS |
| `ValidationError` a media página → `partial` + cursor persistido | `test_backfill_05` | PASS |
| Dry-run no escribe | `test_backfill_07` | PASS |
| Ventana > 92 días → `UserError` | `test_backfill_08` | PASS |
| `base.group_user` no puede crear ni borrar | `test_security_01`, `_02` | PASS |
| Resolver revisión se comprueba en servidor | `test_security_03` | PASS |

## Regresión del módulo base

Evidencia (`artifacts/regression-irg_stripe_subscriptions.txt`):

```
=== CON irg_stripe_payments instalado ===
ERROR: TestStripeSubscriptions.test_10_payment_intent_succeeded_is_deduplicated_by_invoice
0 failed, 1 error(s) of 10 tests

=== BASELINE sin mi modulo (scratch_base_only) ===
ERROR: TestStripeSubscriptions.test_10_payment_intent_succeeded_is_deduplicated_by_invoice
0 failed, 1 error(s) of 10 tests
```

**Resultado idéntico con y sin el módulo nuevo: no es una regresión.**

El criterio del plan («los 10 tests preexistentes verdes sin modificar») **no se puede
cumplir**, porque ya estaba en rojo antes de esta misión. Causa raíz:

`test_10` hace `search([('code','=','stripe')])` y, si encuentra proveedor, solo escribe
`{'state': 'test'}`. Cuando `payment_stripe` está instalado, su fichero de datos ya creó un
`payment.provider` de Stripe **sin claves**, y el constraint exige `stripe_publishable_key` y
`stripe_secret_key` en cuanto el estado deja de ser `disabled` → `ValidationError`. El test
solo pasaba en bases donde ese registro no existía. Como `irg_stripe_subscriptions` depende
(vía `irg_payment_stripe_recurring`) de `payment_stripe`, el fallo se da siempre que el módulo
está bien instalado.

Arreglo (una línea, en el `else` del test): escribir también las claves mock. **Queda fuera
de esta misión** porque el alcance acordado es un módulo nuevo sin tocar los existentes.

## Veredicto

**PASS global para el alcance de la misión.** Instalación limpia, 44/44 tests verdes, y la
única incidencia en el módulo base está demostrada como preexistente mediante comparación
contra una base sin este módulo.

## Pendiente, no cubierto por esta validación

- **T0.3 — enrutado del webhook.** Hay que comprobar en el Dashboard de Stripe que
  `payment_intent.succeeded`, `payment_intent.payment_failed`, `charge.refunded` y
  `checkout.session.completed` están suscritos al endpoint `/stripe/webhook`. Si no lo están,
  el módulo no recibirá nada. Es un paso de despliegue.
- **T0.2 — censo de emails duplicados** sobre datos reales, para decidir si el backfill arranca
  con `email_match_mode=disabled`.
- **Prueba end-to-end con `stripe listen`** contra una cuenta de test de Stripe. No se ha hecho:
  requiere credenciales y el CLI de Stripe. Todos los tests usan Stripe mockeado.
- **Fase 6 (metadata saliente)**, opcional en el plan, sin implementar.
