# Sincronización de nota TFM y create list-safe en Odoo 16

## Contexto reusable

Una sincronización bidireccional entre un expediente y un resultado de libreta
tiene que ser dueña del vínculo en servidor, autorizar al actor antes de
cualquier `sudo` estrecho y adquirir un orden de bloqueo común antes de mutar.
El vínculo no puede viajar en contexto RPC ni en `default_get`.

## Gotcha: One2many `create` en Odoo 16 siempre recibe una lista

`odoo/fields.py` (`One2many.write_real`) llama `comodel.create(to_create)` con
una lista, también cuando el árbol editable solo añade una fila. Un override
`@api.model def create(self, values)` que hace `dict(values)` rompe el árbol
inline y, peor, puede saltarse el rechazo por payload si el bucle asume un
dict. El contrato correcto en 16 es `@api.model_create_multi` sobre
`vals_list`, con rechazo y materialización **por cada dict** antes de mutar.

## Gotcha: refresh de matrícula después del coordinador

`RELEASE SAVEPOINT` no suelta los `FOR UPDATE` de la transacción. Si un
coordinador ya sujetó fases posteriores (resultados) y un `create` mixto
refresca matrículas sin `locked_enrollments`, se toma de nuevo la fase 1. En un
lote `create([{tfm}, {ordinary}])` eso invierte el orden documentado.

Patrón que lo evita en el `create` público mixto: clasificar sin efectos,
crear y refrescar **todas** las filas ordinarias primero, despachar después
cada candidato TFM, y devolver el recordset en el orden de entrada
(`created_by_index`). El `write` mixto TFM/no-TFM se rechaza entero.

Un lote reverse-create de varias cadenas distintas sigue bloqueando cada
identidad en su propio savepoint; el orden global de IDs de matrícula entre
cadenas no queda garantizado. Si hiciera falta el literal del diseño, el
pre-lock de la unión completa iría **antes** de cualquier savepoint de
candidato, sin mutar, y cada coordinador seguiría releyendo tras el lock.

## Guardas de identidad en el padre, no solo en el resultado

Un resultado vinculado hereda alumno/curso/lote de la línea, la libreta, la
admisión y la matrícula. Un `write` o `unlink` en esos padres elude el
`ondelete` del resultado. Un inherit por modelo que llama al mismo
`_irg_tfm_guard_linked_identity` cubre One2many y cascadas. El alcance de
admisiones debe filtrar por triples exactos `(student, course, batch)`, no por
producto cartesiano de `in`.

## Token de diferimiento

Un `object()` comparado con `is` no se puede forjar por JSON-RPC. Hay que
quitarlo del recordset que sale al llamador; no serializa en jobs ni acciones.
