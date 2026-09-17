# Listado Excel de diplomados para informes internos

## Convención

Los listados de alumnos que llegan para informes de diplomado usan una hoja con cabeceras:

- `Correo electrónico`
- `Curso` — nombre largo y código entre paréntesis al final, p. ej. `Diplomado en … (DITGHC2606)`
- `Nombre`
- `País`
- `modalidad`

El código canónico de `op.course.code` es el contenido del último paréntesis. No usar el texto completo de `Curso` como código.

El cruce interno es por correo (normalizado a minúsculas) y ese código. Un informe por listado no debe tomar el lote como origen: en el mismo lote hay alumnos que no van en el Excel.

## Motivo

El personal genera el informe a partir del fichero que le envían, no desde la ficha de `op.batch`.

Implementado en `irg_campus_activity_audit` 16.0.1.1.0.
