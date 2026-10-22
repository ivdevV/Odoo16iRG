# Moroso por cuotas de meses cerrados

Sustituye la cuenta de facturas de `docs/superpowers/specs/2026-10-19-irg-moroso-banner-design.md`. La cinta roja de `docs/superpowers/specs/2026-10-19-irg-moroso-banner-dotado-design.md` no cambia.

## Problema

Cada alumno tiene una factura de oficialidad y otra del máster. Contar facturas publicadas sin pagar marca moroso a quien solo tiene esas dos, aunque esté al corriente. La morosidad es tener cuotas de un mes ya cerrado sin cubrir. El cronograma de estos pedidos suele ser un solo plazo por el importe entero, así que la cuota es cada mes del plazo de pago, no esa línea.

## Alcance

Se modifica `irg_moroso_banner`, versión `16.0.1.4.0`. Pasa a depender también de `isep_sale_subscription_custom` y de `irg_sale_order_extended`.

Incluido:

- La cinta lila decide por meses del plazo de pago que ya cerraron y no están cubiertos por lo cobrado.
- La nota lista cada uno de esos meses con el importe que falta.
- Al actualizar, se recalcula y se anota porque el conjunto de cuotas cambia.

Fuera de alcance:

- La cinta roja **Dotado por morosidad** y la marca `irg_dotado_morosidad` de la factura.
- Contar la cuota del mes en curso, aunque su día de vencimiento ya haya pasado.
- Días de gracia sueltos, distintos del cierre del mes.
- Columna de listado, filtros, portal, correo y actividades pendientes.
- Rehacer el cronograma ni las líneas de la factura.

## Regla

Si el pedido confirmado tiene plazo de pago, cada línea del plazo es una cuota. La fecha sale de calcular el plazo desde `start_date` del pedido (si no hay, desde la fecha del pedido), con el mismo cálculo que usa el plazo para sus vencimientos, día de pago incluido. El importe es el de esa línea sobre el total del pedido.

Lo cobrado es la suma de `amount_total - amount_residual` de las facturas de cliente publicadas del pedido, enlazadas por `order_subscription_id` o por las líneas del pedido. Ese dinero se reparte desde la primera cuota. El resto de una cuota es lo que queda pendiente. Una cuota de importe cero no cuenta.

Cuenta cuando se cumplen las tres condiciones:

- Queda importe pendiente.
- Su vencimiento es anterior al día 1 del mes en curso, según la fecha de la compañía. El 21 de octubre, una cuota del 15 de octubre no cuenta. Una del 15 de septiembre sí. El 1 de noviembre empiezan a contar las de octubre que sigan sin cubrir.
- El pedido está confirmado: `state` en `sale` o `done`.

Si el pedido no tiene plazo de pago, se mantiene la línea de `sale.subscription.schedule` sin pagar o parcial y con `date_due` anterior al día 1. Si el pedido tiene plazo, esas líneas no se suman: un plazo «01 de 01» por el total no es la lista de meses.

Si el contacto es alumno, el pedido pertenece cuando `student_id` o `partner_id` es ese contacto. Si no es alumno, solo cuando `partner_id` es ese contacto. Las cuotas de oficialidad y las del máster suman en la misma cuenta. Un pedido sin factura cuenta todos sus meses ya cerrados.

`irg_is_moroso` es verdadero cuando esa cuenta es al menos 1. La decisión vive en `_irg_partner_should_be_moroso`. La búsqueda usa `sudo()` y no filtra por compañía.

## Nota

Los textos, con N igual a las cuotas pendientes de meses cerrados después del cambio, son:

- «Pasa a moroso. Cuotas vencidas: N.» al pasar a moroso, seguido de una línea por cuota: pedido, fecha de vencimiento e importe pendiente. Si la cuota sale del cronograma porque el pedido no tiene plazo, la línea conserva también la etiqueta del plazo.
- «Cuotas vencidas: N.» con esa misma lista cuando ya era moroso y cambia el conjunto, incluido el importe pendiente de un mes.
- «Deja de ser moroso. Cuotas vencidas: 0.»

Siguen siendo `mail.mt_note` en el contacto y en cada alumno de ese contacto. Se publican cuando cambia el conjunto de cuotas, no solo el sí o no. Las notas antiguas que dicen «Facturas sin pagar» se quedan en el historial.

## Cuándo se recalcula

El mismo método compara el conjunto de cuotas vencidas con el último anotado. Si es el mismo, no escribe y no anota. Para un pedido con plazo, el conjunto incluye el importe pendiente de cada mes.

Se llama para el cliente y el alumno del pedido cuando:

- se crea una cuota de cronograma, o cambian su `date_due`, su `order_id` o su `payment_state`, y el pedido no tiene plazo de pago;
- cambia el `partner_id`, el `student_id`, el `state`, el `payment_term_id` o el `start_date` del pedido;
- se cobra o se deshace el cobro de una factura del pedido. La factura entra por `order_subscription_id` o por sus líneas de venta.

El cron **Recalcular morosos** sigue siendo diario. Recorre los contactos ya marcados, los pedidos confirmados con plazo y `start_date` anterior al día 1, y las cuotas de cronograma de pedidos sin plazo. El día 1 es el cron quien incorpora las cuotas del mes que acaba de cerrar.

Al actualizar a `16.0.1.4.0`, la migración ejecuta ese recálculo con nota. Quien estaba anotado por el plazo único del cronograma recibe la lista de meses que de verdad quedan pendientes.

## Cinta

La lila no cambia de sitio, de texto ni de color. Sigue oculta cuando `irg_is_dotado_morosidad` es verdadero.

## Pruebas

Se sustituyen en la suite las que contaban facturas:

- Cero cuotas vencidas, aunque haya dos facturas impagadas, dejan al contacto al día y no escriben la nota nueva.
- Una cuota sin pagar con vencimiento del mes anterior marca al contacto y al alumno y escribe «Cuotas vencidas: 1.».
- Una cuota pagada solo en parte cuenta igual.
- Una cuota del mes en curso, una pagada, una anulada y una de un pedido en borrador no cuentan.
- Las cuotas de oficialidad y del máster suman. Dos de meses cerrados escriben el número 2.
- El pagador no alumno acumula las de sus pedidos. El alumno acumula las de los pedidos en los que es `student_id`, aunque el cliente sea otro.
- Pagar la cuota vencida quita la cinta y escribe «Deja de ser moroso. Cuotas vencidas: 0.».
- Un segundo recálculo y el cron no duplican la nota.
- La cinta roja sigue tapando a la lila cuando hay una factura dotada.
- Un pedido con plazo de pago y sin factura cuenta cada mes ya cerrado, y no el mes en curso.
- Lo cobrado en la factura se reparte desde el primer mes. El plazo único del cronograma no se suma. El mes a medias sale por el resto, y cubrir los meses cerrados quita la cinta.

## Validación prevista

El diff no añade vistas. El check `e2e_testsprite` se registra `skipped`: el cambio no toca formularios, portal ni assets. Las vistas que ya existen no modifican su comportamiento visible más allá del dato que ya leen.

## Clasificación de entrada

Jev devolvió clase efectiva `full` con vínculo activo y sin aviso de seguridad:

```json
{"status": "ok", "skipped_reason": null, "model": "jev-1.13.0", "mission_class": "full", "mission_class_confidence": 1.0, "mission_class_binding": true, "exceeds_simple_limits": true, "exceeds_simple_noul": 0.87, "needs_security_advisor": false, "security_noul": 0.08, "security_keyword_hit": false, "effective_class": "full", "effective_class_binding": true}
```
