# Cinta roja de dotado en contacto y alumno

Amplía `docs/superpowers/specs/2026-10-19-irg-moroso-banner-design.md`. El módulo sigue siendo `irg_moroso_banner`. La cinta de la factura, en `irg_invoice_dotacion_banner`, no cambia.

## Problema

Si una factura de cliente ya lleva la cinta **Dotado por morosidad**, el contacto y el alumno no deben seguir mostrando la cinta lila **Moroso**. En su lugar se ve una cinta roja con el texto **Dotado por morosidad**, aunque el asiento de dotación haya dejado esa factura pagada.

## Alcance

Se modifica `irg_moroso_banner`. Pasa a depender también de `irg_invoice_dotacion_banner`. Versión `16.0.1.1.0`.

Incluido:

- Campo guardado `res.partner.irg_is_dotado_morosidad`.
- Cinta roja **Dotado por morosidad** en el formulario de contacto y en el de alumno.
- La cinta lila queda oculta mientras la roja está activa.
- Recálculo cuando cambia la marca de la factura, con el mismo cron y los mismos ganchos de contacto y alumno.
- Nota interna solo cuando el valor cambia después de instalar o actualizar.

Fuera de alcance:

- Cambiar la cinta gris de la factura.
- Cambiar el umbral ni los estados que deciden la cinta lila.
- Apagar `irg_is_moroso` porque exista una factura dotada. La lila se oculta; el booleano de moroso sigue su regla.
- Columna de listado, filtros, portal, correo y actividades pendientes.

## Regla

`irg_is_dotado_morosidad` es verdadero cuando hay al menos una factura de cliente con `irg_dotado_morosidad` activo. No importa `payment_state` ni si está pagada.

El vínculo con el contacto es el de la cinta lila:

- Si existe un `op.student` con ese `partner_id`, cuentan las facturas cuyo `partner_id` es el contacto y las cuyo `irg_student_partner_id` es el contacto.
- Si el contacto no es alumno, solo cuentan las facturas cuyo `partner_id` es el contacto.

Consecuencia aceptada: el pagador y el alumno pueden llevar los dos la cinta roja si la factura está vinculada a los dos. Una sola factura basta. No hay umbral de dos.

No se filtra por compañía. La búsqueda usa `sudo()`.

La decisión vive en `_irg_partner_should_be_dotado`.

## Dato

`irg_is_dotado_morosidad` es un booleano almacenado en `res.partner`, con valor inicial falso, `copy=False` e índice. No lleva `tracking=True`. El alumno no tiene un segundo campo: la vista lee el booleano del contacto.

`irg_is_moroso` no cambia de significado.

## Cuándo se recalcula

`_irg_recompute_dotado(notify=True)` compara la regla con el valor guardado. Si no cambia, no escribe y no anota. Si cambia, guarda el booleano y, cuando `notify` es verdadero, publica la nota.

Se llama para el contacto cliente y para el alumno vinculado, dentro de la misma transacción, cuando:

- se escribe `irg_dotado_morosidad` en un `account.move`;
- se crea o se borra un `account.move`, o cambian su `partner_id` o su `irg_student_partner_id`;
- se crea un `op.student` o cambia su `partner_id`.

El cron **Recalcular morosos** incluye también los contactos que ya tienen la marca y los de las facturas con `irg_dotado_morosidad` activo. Usa el mismo método, con nota si el valor cambia.

Al instalar, el `post_init_hook` ejecuta ese recálculo con `notify=False`. Al actualizar desde `16.0.1.0.0`, una migración `16.0.1.1.0` hace lo mismo. Quien ya tenga una factura dotada recibe la cinta y no recibe nota.

## Nota

Subtipo `mail.mt_note`, en el contacto y en cada `op.student` de ese contacto, incluidos los archivados. No envía correo.

Textos:

- «Pasa a dotado por morosidad.»
- «Deja de estar dotado por morosidad.»

El autor es el usuario interno actual. En el cron, el superusuario. La instalación y la actualización no publican esta nota.

La nota de moroso sigue publicándose cuando `irg_is_moroso` cambia. Si en la misma operación alguien pasa a moroso y a dotado, se escriben las dos notas y en la ficha solo se ve la cinta roja.

## Cinta

En `base.view_partner_form` y en `openeducat_core.view_op_student_form`:

- La cinta lila **Moroso** sigue en su sitio y queda invisible si `irg_is_moroso` es falso o si `irg_is_dotado_morosidad` es verdadero.
- Después va la cinta `web_ribbon` con título **Dotado por morosidad**, `bg_color="bg-danger"` y visible solo cuando `irg_is_dotado_morosidad` es verdadero.

`bg-danger` es el rojo de Odoo. El campo va en la vista, invisible. La cinta sigue visible si el registro está archivado. No hay cinta en el portal.

## Pruebas

Se añaden a la suite de `irg_moroso_banner`:

- Sin facturas dotadas no hay marca ni nota.
- Una factura dotada y ya pagada marca al contacto y al alumno, escribe una sola nota y no muestra la condición de la cinta lila como única cinta visible.
- Una factura dotada que además está impagada muestra la roja. Con una sola impagada, `irg_is_moroso` sigue en falso.
- Dos facturas impagadas sin dotar siguen mostrando solo la lila.
- Con dos impagadas y otra dotada, `irg_is_moroso` puede quedar verdadero y la cinta lila queda oculta por la roja.
- Quitar la marca de la factura apaga la roja, escribe «Deja de estar dotado por morosidad.» y, si siguen dos impagadas, la lila vuelve a poder verse.
- El pagador no alumno y el alumno vinculado reciben la marca según la regla de cada uno.
- Duplicar el contacto no copia la marca.
- Un segundo recálculo sin cambio no escribe otra nota.
- El recálculo con `notify=False` pone la marca y no escribe nota.
- Los dos formularios contienen `title="Dotado por morosidad"`, `bg-danger` y la cinta lila condicionada a que `irg_is_dotado_morosidad` sea falso.

## Validación prevista

El diff toca vistas de formulario. El plan incluye `e2e_testsprite` con `projectPath` en `addons-extra/extrairg/irg_moroso_banner`.

## Clasificación de entrada

Jev devolvió clase efectiva `full` con vínculo activo y sin aviso de seguridad:

```json
{"status": "ok", "skipped_reason": null, "model": "jev-1.13.0", "mission_class": "full", "mission_class_confidence": 1.0, "mission_class_binding": true, "exceeds_simple_limits": true, "exceeds_simple_noul": 0.89, "needs_security_advisor": false, "security_noul": 0.2, "security_keyword_hit": false, "effective_class": "full", "effective_class_binding": true}
```
