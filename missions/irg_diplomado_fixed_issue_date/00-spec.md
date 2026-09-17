# Spec — irg_diplomado_fixed_issue_date

## Problema

La línea «Barcelona, a …» de los diplomas de diplomados usa `issue_date`.
Hoy ese campo toma el día de generación (`fields.Date.context_today`), así que
la fecha impresa cambia según el día en que se emite el diploma.

## Comportamiento requerido

- Día y mes fijos: **26 de septiembre**.
- Año variable: el **año del día en que se genera** el diploma
  (`fields.Date.context_today`). Ejemplo: si se genera el 31/08/2026,
  el diploma debe decir «Barcelona, a 26 de Septiembre de 2026»;
  si se genera en 2027, el año pasa a 2027.
- Al generar desde el asistente se fuerza esa fecha aunque el usuario
  (o una llamada RPC) ponga otra. El campo queda de solo lectura.
- Un diplomado nuevo creado sin `issue_date` (p. ej. portal) usa el mismo
  valor por defecto.
- Los registros ya emitidos **no se reescriben**. Reimprimir un PDF
  existente descarga el adjunto que ya tiene. Un `create` de registro
  con `issue_date` explícita (tests, datos históricos) conserva esa fecha.
- Destino de publicación: **Dev (`Dev_iRG`) primero**. Producción fuera
  de alcance hasta autorización posterior.

## Fuera de alcance

- Cambiar el formato largo de `_format_issue_date` (se mantiene
  «26 de Septiembre de {año}»).
- Diplomas de máster (`irg_generacion_diplomas`).
- Reescribir PDFs ya generados.
- Commit, push o PR sin autorización explícita. Push a `Dev_iRG` solo
  con OK nuevo del usuario.
