# Cinta de moroso en contacto y alumno

## Problema

Secretaría necesita ver, al abrir un contacto o un alumno de OpenEduCat, si esa persona es morosa. La señal es la cinta diagonal de Odoo, en lila, con el texto **Moroso**. El cambio de estado queda anotado en el historial del contacto y, si existe, en el del alumno.

`irg_student_payment_status` ya marca morosos con otra regla (facturas vencidas, 15 días de gracia, estados intermedios y una actividad pendiente). Este trabajo no lo modifica. Conviven si ambos están instalados: en el alumno pueden verse las dos cintas.

## Alcance

Módulo nuevo `irg_moroso_banner` en `addons-extra/extrairg/`.

Dependencias: `account`, `openeducat_core`, `irg_student_invoice_payment_link`.

Incluido:

- Campo guardado `res.partner.irg_is_moroso`.
- Cinta lila **Moroso** en el formulario de contacto y en el de alumno, solo cuando el campo está activo.
- Recálculo al crear, modificar o borrar un asiento, al crear un alumno o cambiar su contacto, más un cron diario y un cálculo inicial al instalar.
- Nota interna en el historial cuando el valor cambia.

Fuera de alcance:

- El asiento «Dotación por Morosidad» no decide por sí solo quién es moroso. La cinta roja que lo sustituye en el contacto y en el alumno está en `docs/superpowers/specs/2026-10-19-irg-moroso-banner-dotado-design.md`.
- Cualquier cambio en `irg_student_payment_status`.
- Columna de listado, filtros, botón manual, portal web, correo y actividades pendientes.
- Agrupar facturas por entidad comercial (`commercial_partner_id`). La cuenta usa el `partner_id` exacto de la factura.

## Regla

La cuenta de facturas de esta spec queda sustituida por las cuotas de meses cerrados en `docs/superpowers/specs/2026-10-19-irg-moroso-cuotas-design.md`. Lo que sigue en esta sección es la regla anterior.

Entran facturas de cliente publicadas (`account.move.state = posted`, `move_type = out_invoice`) con `payment_state` en `not_paid` o `partial`.

No entran borradores, canceladas, rectificativas (`out_refund`), facturas pagadas, revertidas ni facturas con cobro registrado pendiente de conciliar (`in_payment`).

Dos dominios, según el contacto:

- Si existe un `op.student` con `partner_id` igual a ese contacto, cuentan las facturas cuyo `partner_id` es el contacto y las cuyo `irg_student_partner_id` es el contacto. Ese campo, definido en `irg_student_invoice_payment_link`, es un `Many2one` a `res.partner` y sale del `student_id` del pedido.
- Si el contacto no es alumno, solo cuentan las facturas cuyo `partner_id` es el contacto.

Consecuencia aceptada: un pagador con dos facturas impagadas de dos alumnos distintos queda moroso en su contacto. Cada alumno queda moroso solo si a él le corresponden dos o más. Si las dos facturas son del mismo alumno, quedan morosos el pagador y ese alumno.

La decisión vive en un método de `res.partner`, `_irg_partner_should_be_moroso`. La implementación de este módulo devuelve verdadero cuando la cuenta de facturas alcanza el umbral. Otro módulo puede heredarlo, llamar a `super` y añadir una causa propia. La nota de este módulo sigue citando el número de facturas que cuenta esta regla.

## Dato

`irg_is_moroso` es un booleano almacenado en `res.partner`, con valor inicial falso, `copy=False` e índice. El alumno no tiene un segundo campo: `op.student` delega en `res.partner` mediante `_inherits`, y la vista del alumno lee ese mismo booleano.

No lleva `tracking=True`. La única constancia es la nota redactada, para no duplicar el historial.

## Cuándo se recalcula

El método `_irg_recompute_moroso` compara la regla con el valor guardado. Si no cambia, no escribe y no anota. Si cambia, guarda el booleano y publica la nota.

Se llama, dentro de la misma transacción, cuando:

- se crea o se borra un `account.move`, para su `partner_id` y su `irg_student_partner_id`;
- se modifica un `account.move` y cambia `state`, `payment_state`, `partner_id`, `move_type` o `irg_student_partner_id`, para los valores actuales y para los anteriores de `partner_id` e `irg_student_partner_id`;
- se crea un `op.student`, o cambia su `partner_id`, para el contacto nuevo y el anterior.

Una factura en borrador dispara el recálculo al crearse, pero la regla no la cuenta hasta que esté publicada. La cuenta no filtra por compañía: entran las facturas que cumplen el dominio en cualquier compañía.

La búsqueda de facturas usa `sudo()`, para que una regla de registro contable no oculte facturas y deje el marcador corto. Quien abre la ficha solo lee el booleano y no necesita permiso de contabilidad. Si el recálculo falla, la operación que lo disparó se deshace entera.

El cron **Recalcular morosos** está activo, es diario y lleva `noupdate="1"`. Recorre solo tres conjuntos, sin duplicar notas porque usa el mismo método:

- contactos con `irg_is_moroso` activo;
- `partner_id` de facturas de cliente publicadas en `not_paid` o `partial`;
- `irg_student_partner_id` de esas mismas facturas.

Al instalar, un `post_init_hook` ejecuta ese mismo recálculo. Quien ya supere el umbral pasa de falso a verdadero y recibe una sola nota. Es la clasificación inicial, no una nota repetida en cada arranque.

## Nota

Subtipo `mail.mt_note`. No envía correo al alumno ni al pagador.

Textos, con N igual a la cuenta de esta regla después del cambio:

- «Pasa a moroso. Facturas sin pagar: N.»
- «Deja de ser moroso. Facturas sin pagar: N.»

La nota se publica en el contacto y en cada `op.student` cuyo `partner_id` sea ese contacto. La publicación usa `sudo()` para que el cron y un usuario sin derechos de seguidor puedan dejarla. El autor es el usuario interno actual. En el cron y en el cálculo de la instalación, el autor es el superusuario.

## Cinta

Widget `web_ribbon`, título **Moroso**, visible solo cuando `irg_is_moroso` es verdadero. El campo va en la vista, invisible, porque la condición de la cinta lo necesita.

El lila es la clase `irg_bg_moroso` en los assets de backend: fondo `#7C5CBF`, texto `#FFFFFF`.

Herencias, ambas después de la cinta de archivado:

- `base.view_partner_form`
- `openeducat_core.view_op_student_form`

La cinta sigue visible si el registro está archivado. Puede coincidir con la cinta roja de archivado y, en el alumno, con la cinta de `irg_student_payment_status`. El xpath cuelga de la vista de OpenEduCat o de la de contactos, no de la vista del otro módulo.

No hay cinta en el portal web.

## Estructura

```text
addons-extra/extrairg/irg_moroso_banner/
  __init__.py
  __manifest__.py
  models/res_partner.py
  models/account_move.py
  models/op_student.py
  data/ir_cron.xml
  views/res_partner_views.xml
  views/op_student_views.xml
  static/src/scss/moroso_ribbon.scss
  tests/__init__.py
  tests/test_moroso_banner.py
```

Versión del manifiesto: `16.0.1.0.0`. No hay modelo nuevo ni `ir.model.access.csv`: el campo sigue los permisos de `res.partner`.

## Pruebas

Suite en el módulo, con `TransactionCase`:

- Cero o una factura publicada e impagada dejan el contacto al día y no escriben nota.
- Dos facturas impagadas lo marcan moroso y escriben la nota en el contacto y en el alumno, con el número 2.
- Una factura cobrada solo en parte cuenta igual que una impagada.
- Un borrador, una rectificativa y una factura en `in_payment` no cuentan.
- Una factura cuyo cliente es el pagador y cuyo `irg_student_partner_id` es el alumno cuenta para el alumno. El pagador, si no es alumno, solo acumula las suyas.
- Dos facturas de dos alumnos distintos marcan al pagador y no marcan a un hijo que solo tiene una.
- Bajar de dos a una quita el marcador y escribe «Deja de ser moroso».
- Un segundo recálculo sin cambio de estado no escribe otra nota.
- Cambiar el cliente o el alumno vinculado, o borrar la factura, recalcula quien sale y quien entra.
- Un contacto que no es alumno y llega a dos facturas queda moroso solo en su ficha.
- Crear el `op.student` de un contacto que ya acumula dos facturas vinculadas aplica el dominio de alumno en ese momento.
- El cron no duplica una nota ya escrita.

## Validación prevista

El diff toca vistas de formulario, así que el plan de implementación debe incluir el check `e2e_testsprite` además de las pruebas del módulo. `projectPath` será el directorio de `irg_moroso_banner`.

## Clasificación de entrada

Jev, sobre la petición original, devolvió clase efectiva `full` con vínculo activo y sin aviso de seguridad:

```json
{"status": "ok", "skipped_reason": null, "model": "jev-1.13.0", "mission_class": "full", "mission_class_confidence": 0.99, "mission_class_binding": true, "exceeds_simple_limits": true, "exceeds_simple_noul": 0.96, "needs_security_advisor": false, "security_noul": 0.09, "security_keyword_hit": false, "effective_class": "full", "effective_class_binding": true}
```
