# Cinta de dotación por morosidad en la factura

## Problema

Secretaría necesita ver, al abrir una factura de cliente, si esa factura tiene aplicada la dotación por morosidad. La señal es la cinta diagonal de Odoo, con el texto **Dotado por morosidad**. El cambio queda anotado en el historial de la factura.

El asiento real es un asiento manual publicado, como `AMAN/2025/12/0107`. Su referencia y la etiqueta de sus apuntes contienen «Dotación por morosidad». Cada abono de la cuenta 430 queda conciliado con el apunte de cliente de una factura. Un mismo asiento dota muchas facturas.

Este trabajo no marca contactos ni alumnos, y no modifica `irg_moroso_banner` ni `irg_student_payment_status`. El tipo financiero «Devoluciones a pagar» no es la señal: lo calcula `account_tax_balance` porque la 430 va al haber.

## Alcance

Módulo nuevo `irg_invoice_dotacion_banner` en `addons-extra/extrairg/`.

Dependencia: `account`.

Incluido:

- Campo guardado `account.move.irg_dotado_morosidad`.
- Cinta **Dotado por morosidad** en el formulario de la factura, solo cuando el campo está activo.
- Recálculo al crear o borrar la conciliación, al publicar el asiento, al pasarlo a borrador, al cambiar su referencia y al cambiar la etiqueta de un apunte.
- Cálculo inicial al instalar, sin nota.
- Una nota interna en la factura cuando el valor cambia después de instalar.

Fuera de alcance:

- Cinta en el contacto, en el alumno, en el asiento de la dotación, en abonos y en facturas de proveedor.
- Cualquier cambio en `irg_moroso_banner` o en `irg_student_payment_status`.
- Columna de listado, filtros, botón manual, portal web, correo, actividades pendientes y cron diario.
- Tratar «Dotacion» sin tilde como equivalente.

## Regla

La frase es la constante `_IRG_DOTACION_PHRASE = 'dotación por morosidad'`.

`irg_dotado_morosidad` es verdadero solo en un `account.move` con `move_type = out_invoice` que tenga al menos un apunte conciliado, total o parcialmente, con un apunte de otro asiento. Ese otro asiento está publicado (`state = posted`) y cumple una de estas dos condiciones, sin distinguir mayúsculas:

- su `ref` contiene la frase;
- el `name` del apunte conciliado contiene la frase.

La comparación es `ilike` sobre `%dotación por morosidad%`. PostgreSQL no ignora la tilde, así que «Dotacion por morosidad» no cuenta. «Dotación por Morosidad alumnos IRG 31/12/25» sí cuenta.

No se filtra por compañía: la conciliación ya señala los dos asientos. No hace falta que la factura esté pagada del todo. Un pago o un asiento conciliado que no contiene la frase no marca la factura, aunque su `payment_state` sea `paid`. Varias conciliaciones con la misma frase dejan un solo verdadero. El asiento de la dotación, el abono (`out_refund`) y la factura de proveedor quedan en falso.

La decisión vive en `_irg_move_is_dotado_morosidad`.

## Dato

`irg_dotado_morosidad` es un booleano almacenado en `account.move`, con valor inicial falso, `copy=False` e índice. No lleva `tracking=True`. La única constancia es la nota redactada.

No hay modelo nuevo ni `ir.model.access.csv`: el campo sigue los permisos de `account.move`.

## Cuándo se recalcula

`_irg_recompute_dotacion(notify=True)` compara la regla con el valor guardado. Si no cambia, no escribe y no anota. Si cambia, guarda el booleano y, cuando `notify` es verdadero, publica la nota.

Se llama, dentro de la misma transacción, cuando:

- se crea o se borra un `account.partial.reconcile`, para cada factura de cliente de los dos asientos conciliados;
- se modifica un `account.move` y cambia `state` o `ref`, para las facturas de cliente conciliadas con ese asiento y, si el asiento modificado es una factura de cliente, para ella misma;
- se modifica el `name` de un `account.move.line`, para las facturas de cliente conciliadas con ese apunte.

La búsqueda de conciliaciones y la escritura del booleano usan `sudo()`, para que una regla de registro no deje el marcador corto. Quien abre la factura solo lee el booleano. Si el recálculo falla, la operación que lo disparó se deshace entera.

Al instalar, un `post_init_hook` ejecuta el mismo recálculo con `notify=False`. Las facturas que ya cumplen la regla pasan a verdadero y no reciben nota. No hay cron.

## Nota

Subtipo `mail.mt_note`, en la factura. No envía correo y no crea actividad.

Textos:

- «Pasa a dotado por morosidad.»
- «Deja de estar dotado por morosidad.»

La publicación usa `sudo()`. El autor es el usuario interno actual. La instalación no publica notas, así que no necesita autor.

## Cinta

Widget `web_ribbon` en `account.view_move_form`, título **Dotado por morosidad**, visible solo cuando `irg_dotado_morosidad` es verdadero. El campo va en la vista, invisible, porque la condición de la cinta lo necesita.

La cinta se inserta después de la última `web_ribbon` de `account.view_move_form`. En la vista base esa última cinta es «Invoicing App Legacy». Odoo no permite usarla de selector porque `text` es traducible. Así «Dotado por morosidad» queda por encima de «Pagada» cuando la factura está pagada y dotada a la vez. Esas cintas siguen en el formulario.

El color es la clase `irg_bg_dotado` en los assets de backend: fondo `#4F6D7A`, texto `#FFFFFF`.

No hay cinta en el listado ni en el portal.

## Estructura

```text
addons-extra/extrairg/irg_invoice_dotacion_banner/
  __init__.py
  __manifest__.py
  models/__init__.py
  models/account_move.py
  views/account_move_views.xml
  static/src/scss/dotacion_ribbon.scss
  tests/__init__.py
  tests/test_invoice_dotacion_banner.py
```

`models/account_move.py` hereda `account.move`, `account.move.line` y `account.partial.reconcile`. El `post_init_hook` vive en `__init__.py`.

Versión del manifiesto: `16.0.1.0.0`. Licencia LGPL-3. Autor iRG.

## Pruebas

Suite en el módulo, con `TransactionCase`:

- Una factura de cliente sin conciliación queda en falso y sin nota.
- Conciliarla con un asiento publicado cuya `ref` contiene la frase la marca y escribe «Pasa a dotado por morosidad.» una sola vez.
- La frase solo en el `name` del apunte conciliado también la marca.
- Una diferencia de mayúsculas cuenta. La frase sin tilde no cuenta.
- Una conciliación parcial cuenta.
- Un pago conciliado que no contiene la frase no marca la factura.
- Quitar la conciliación, pasar el asiento a borrador o borrar la frase de la referencia y de la etiqueta apaga la marca y escribe «Deja de estar dotado por morosidad.».
- Varias líneas del mismo asiento dejan una sola nota.
- El asiento de la dotación, un abono y una factura de proveedor quedan en falso.
- Duplicar la factura no copia la marca.
- Un segundo recálculo sin cambio no escribe otra nota.
- El cálculo de instalación pone la marca en una factura ya conciliada y no escribe nota.
- El formulario contiene `title="Dotado por morosidad"` y la clase `irg_bg_dotado`.

## Validación prevista

El diff toca una vista de formulario, así que el plan de implementación incluye el check `e2e_testsprite` además de las pruebas del módulo. `projectPath` será el directorio de `irg_invoice_dotacion_banner`.

## Clasificación de entrada

Jev, sobre este módulo, devolvió clase efectiva `full` con vínculo activo y sin aviso de seguridad:

```json
{"status": "ok", "skipped_reason": null, "model": "jev-1.13.0", "mission_class": "full", "mission_class_confidence": 1.0, "mission_class_binding": true, "exceeds_simple_limits": true, "exceeds_simple_noul": 0.95, "needs_security_advisor": false, "security_noul": 0.07, "security_keyword_hit": false, "effective_class": "full", "effective_class_binding": true}
```
