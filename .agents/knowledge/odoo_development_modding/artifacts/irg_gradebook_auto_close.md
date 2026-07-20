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

## Gotcha reproducido en Dev: el template de línea puede ampliar por error el principal

La libreta `AD003762` mostraba en cabecera el template principal `Solo Examen`, pero
una de sus asignaturas (`op.subject`) conservaba internamente un template mixto de
Asignación y Examen. El cálculo base de `app.gradebook.subject.compute_data_show()`
tomaba el template de la asignatura y dejaba `show_assignment=True`. Como consecuencia,
el autocierre exigía una asignación ausente aunque la libreta principal no contemplaba
esa categoría.

No debe corregirse este caso cambiando solo los datos de la asignatura: la combinación
puede volver a aparecer y el encabezado de la libreta es el contrato que limita las
categorías exigibles.

## Patrón: categorías efectivas por intersección (ceiling)

Cuando existe un template principal, calcular los tipos efectivos de cada línea como:

```text
effective_types = main_template_types ∩ line_template_types
```

Si la línea no tiene template propio, usar los tipos principales como tipos de línea,
de modo que herede todos los requisitos. Si falta el template principal, conservar el
resultado base del compute: sin ese techo no hay una regla principal segura que aplicar.

Este patrón aporta una precedencia asimétrica e intencionada:

- el template principal es el techo y una línea nunca puede añadir categorías;
- el template de línea puede eliminar categorías para excepciones como Prácticas/TFM;
- el cálculo se aplica de forma uniforme a `assignment`, `exam`, `interaction` y
  `foro`;
- el cierre continúa pasando por `_irg_is_ready_to_close()` y `state_to_done()`.

La razón para extender el compute, en vez de duplicar la regla solo dentro del
autocierre, es mantener coherentes la visibilidad funcional de la línea, la condición
previa del addon y las validaciones estándar de `isep_gradebook`.

La instalación o actualización del addon no realiza un barrido retroactivo. Las
libretas existentes se vuelven a evaluar únicamente tras una mutación posterior de
`app.gradebook.result`.

## Gotcha: un cambio de compute no sanea necesariamente valores stored existentes

Los campos `show_assignment`, `show_exam`, `show_interaction` y `show_foro` ya eran
computed stored antes de añadir la regla de intersección. Tras actualizar el addon,
una línea creada con la lógica antigua puede conservar en PostgreSQL, por ejemplo,
`show_assignment=True` aunque el template principal actual sea `Solo Examen`.

Confiar solo en el nuevo `@api.depends` no resuelve necesariamente ese histórico: si
ninguna dependencia cambia después del upgrade, el ORM puede leer el valor persistido
antiguo y la condición de autocierre observar una categoría obsoleta.

## Patrón: refresco de la libreta afectada antes de evaluar readiness

En un efecto derivado disparado por mutaciones del hijo, refrescar explícitamente los
campos computed stored de las líneas afectadas inmediatamente antes de evaluar la
condición agregada:

```text
result create/write/unlink
  -> affected in-progress gradebook
  -> gradebook_subject_ids.compute_data_show()
  -> _irg_is_ready_to_close()
  -> state_to_done()
```

La frontera importa:

- usar el recordset `gradebook.gradebook_subject_ids` ya afectado por el trigger;
- omitir el compute para libretas finalizadas o vacías;
- no usar `search()` global, migración ni barrido durante instalación/upgrade;
- mantener el refresco antes de readiness para que la decisión consuma valores
  actuales, incluida la intersección de templates.

El coste queda acotado a O(líneas de las libretas afectadas) y el siguiente cambio de
resultado sanea de forma oportunista una libreta antigua. Esto preserva el requisito
de no hacer un barrido global y evita que un stale stored bloquee el autocierre.
