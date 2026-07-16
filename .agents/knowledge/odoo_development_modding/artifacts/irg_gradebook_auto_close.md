# Autocierre seguro tras mutaciones de resultados Odoo

## Contexto reusable

Cuando una decisión agregada depende de campos computed stored de registros hijos,
el trigger puede vivir después de `create`, `write` y `unlink` del hijo. La decisión
debe ejecutarse después de `super()` y reunir todas las relaciones afectadas:

- en `write`, conservar la relación anterior y unirla con la posterior;
- en `unlink`, conservar la relación antes de borrar y filtrar con `exists()` después;
- en operaciones multi-registro, revisar si el override heredado es realmente
  compatible con recordsets; un método base que accede a una relación singleton puede
  exigir delegación por registro.

## Gotcha: el create base puede provocar writes internos

Un `create` heredado no siempre es atómico desde el punto de vista de los hooks. En
`app.gradebook.result`, el create base puede volver a escribir `scoring_total` para
aplicar redondeo. Ese write ORM entra en cualquier override de `write` mientras el
create exterior todavía está construyendo el lote.

Si el write anidado dispara una decisión agregada, puede observar solo el primer
elemento y cerrar prematuramente una libreta. Un elemento posterior puede cambiar el
promedio, dejando el estado cerrado inconsistente con el resultado final del lote.

## Patrón: diferimiento namespaced y rebrowse limpio

Para diferir únicamente el efecto agregado sin saltarse la lógica base:

1. Ejecutar el create base con una clave de contexto namespaced y específica del
   addon, por ejemplo `irg_<addon>_skip_nested_<effect>`.
2. En `write`, ejecutar siempre `super()` completo. Si está la clave, omitir solo el
   efecto posterior que no debe observar el lote parcial.
3. Tras cada create base, rebrowsear los IDs desde un recordset con el contexto normal.
   No unir directamente el recordset contextual devuelto, porque el contexto puede
   propagarse al resultado exterior y a futuras operaciones.
4. Al terminar todo el lote, reunir las relaciones desde los registros rebrowseados y
   ejecutar una sola vez el efecto agregado en contexto normal.
5. Añadir una regresión `@api.model_create_multi` que combine un primer valor que
   haría disparar el efecto con un valor posterior que lo invalide, y afirmar también
   que la clave interna no aparece en `records.env.context`.

Este patrón conserva la lógica base de redondeo y cualquier write externo normal; solo
difiere el efecto derivado durante la ventana del create exterior. La clave interna no
debe documentarse como API pública ni reutilizarse fuera del addon.

## Validación de cierres que no deben abortar el guardado

Si el método canónico de transición aplica validaciones de negocio, debe reutilizarse
en lugar de escribir el estado directamente. Cuando el intento automático no deba
invalidar la mutación principal, capturar únicamente la excepción de negocio esperada
(`UserError` en este caso), registrar el motivo y dejar el registro sin transicionar.
No usar `except Exception`, porque ocultaría defectos de programación o infraestructura.
