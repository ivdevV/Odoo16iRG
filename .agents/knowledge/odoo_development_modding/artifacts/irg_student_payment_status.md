# Patrones para deuda agregada, acciones con `sudo()` y actividades reincidentes

## Residuales multimoneda en moneda de compañía

Cuando una métrica agrega deuda de `account.move` de distintas monedas y el
campo de salida usa la moneda de la compañía, se debe sumar
`amount_residual_signed`, no `amount_residual`. El primero representa el
residual firmado en moneda de compañía; el segundo está expresado en la moneda
de cada factura y no se puede agregar directamente.

El mismo importe y la misma moneda deben usarse en el compute, el chatter y
cualquier salida visual. Un test útil crea una factura extranjera con una tasa
conocida y verifica que el residual de compañía difiere del residual de
factura; así detecta errores que una suite monomoneda no revela.

## Autorización antes de elevar privilegios

Un método público que termina llamando helpers con `sudo()` debe autorizar el
recordset original antes de entrar en esa ruta. Para una acción de escritura,
el orden reutilizable es:

1. comprobar el grupo funcional con `has_group()`;
2. ejecutar `check_access_rights('write')`;
3. ejecutar `check_access_rule('write')` sobre todos los registros objetivo;
4. solo entonces llamar al servicio interno que limita `sudo()` a las
   operaciones necesarias.

Comprobar únicamente el grupo o usar `sudo()` antes de las reglas permite
saltar ACL o record rules. Los atributos `groups` de una vista son solo UX y no
protegen llamadas ORM/RPC. La suite debe demostrar tres casos: rechazo por
grupo sin mutación, usuario de grupo permitido con escritura y rechazo por una
regla de registro de escritura.

## Actividades idempotentes que admiten reincidencia

Para representar una incidencia abierta, la idempotencia debe buscar solo la
actividad pendiente propia por una identidad estable: tipo, modelo, `res_id` y
resumen. Al resolverse la condición, se debe completar con
`action_feedback()` en vez de borrar la actividad. Esto conserva la auditoría
y elimina la actividad de pendientes.

Si la condición reaparece, la búsqueda ya no encuentra una actividad abierta
y puede crear otra. Mientras la condición no cambie, ejecuciones repetidas no
duplican el seguimiento. El test debe recorrer el ciclo completo: entrada,
rerun idempotente, salida con feedback, reincidencia y segundo rerun.

## Gotchas

- Sumar residuales de factura y mostrarlos con moneda de compañía produce un
  valor silenciosamente incorrecto en entornos multimoneda.
- Buscar actividades sin una identidad suficientemente específica puede
  cerrar tareas ajenas o impedir seguimientos futuros.
- Borrar la actividad resuelta pierde trazabilidad; dejarla pendiente impide
  distinguir una reincidencia real.
- La notificación del usuario asignado pertenece al comportamiento estándar de
  `mail.activity`; no debe confundirse con una campaña de email del módulo.

## Evidencia de referencia

- Misión: `missions/student-payment-status/`.
- Suite funcional: 15 tests, 0 fallos y 0 errores, incluidos multimoneda,
  grupo/ACL/record rules y ciclo completo de actividad.
- Validación UI: residual en moneda de compañía, chatter y actividad pendientes
  observados en navegador.
