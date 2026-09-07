# Patron: no reservar valores Selection que Python y QWeb interpretan distinto

Fecha: 2026-09-07

Modulo: `irg_practice_agreement_specific`

## Decision reutilizable

No añadir a un `Selection` un valor «reservado para más adelante» si el
código Python ya lo trata como un caso (p. ej. `_is_especifico()`) y las
plantillas QWeb aún no. Ese valor es seleccionable en el formulario y
genera un documento con el clausulado equivocado y el nombre correcto.

Hasta que exista plantilla y flujo, el valor no debe estar en
`selection_add`. Un test `assertNotIn('valor_reservado', dict(field.selection))`
evita reintroducirlo.

## Motivos

Se pensó dejar `especifico_nacional` en la selección para la siguiente
entrega. Python lo incluía en los tipos con doble firma; el report y el
portal solo sustituían el cuerpo si el tipo era `especifico_internacional`.
El PDF salía con cláusulas de convenio marco y nombre de específico nacional.
