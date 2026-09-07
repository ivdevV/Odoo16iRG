# Progreso real de curso y disparadores de calificación

## Campo canónico

En esta instancia el porcentaje por matrícula es
`op.student.course.completion_porc`, definido por `isep_student_filter`. No existe
`completion_proc`. El campo es calculado, no almacenado y no tiene método `search`,
por lo que no debe aparecer en dominios ORM que se traduzcan a SQL.

Un addon que lo consuma debe declarar directamente `isep_student_filter`. Si además
hereda la libreta, debe declarar también `isep_gradebook`; no debe confiar en una
cadena transitiva a través de otro addon.

## Activación derivada de notas

`completion_porc` cuenta asignaturas obligatorias cuyo
`app.gradebook.subject.final_subject_note` almacenado es al menos 8. Para ejecutar
una acción justo al cruzar un porcentaje:

1. Heredar `app.gradebook.result.create/write/unlink` y actuar después de `super()`.
2. En `write`, conservar las asignaturas anterior y posterior si cambia la relación.
3. Derivar las parejas alumno+curso desde esas asignaturas; el progreso no tiene
   dimensión de lote.
4. Bloquear las matrículas exactas por ID y en orden estable para serializar notas
   concurrentes.
5. Recalcular explícitamente `final_subject_note`, hacer `flush_recordset`, invalidar
   `completion_porc` y leerlo con permisos acotados a esas matrículas.
6. Mantener un cron paginado sin filtro de porcentaje como recuperación para cambios
   por SQL u otros procesos que eludan el ORM.

El `create` base de `app.gradebook.result` puede hacer un `write` interno para
normalizar `scoring_total`. Use una clave de contexto namespaced para diferir solo el
efecto derivado y ejecutarlo una vez al terminar; el patrón general también está
documentado en `irg_gradebook_auto_close.md`.
