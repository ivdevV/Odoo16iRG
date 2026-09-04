# Patron: Fecha de inicio de clases en diplomas de diplomados

Fecha: 2026-09-04

Modulo: `irg_generacion_diplomados_class_start_date`

## Decision reutilizable

El texto «celebrado del …» de un diploma de diplomado usa
`op.batch.date_start_class`, no `op.batch.start_date`. Si `date_start_class`
esta vacio, el fallback es `start_date`.

El PDF emitido vive en `irg.diplomado.registry.attachment_id`. El boton
Reimprimir siempre regenera. La descarga de portal solo regenera si falta el
PDF o si `registry.start_date` esta informado y desfasado respecto al lote.
Asi no se rompen tests de portales que crean un adjunto con `start_date` vacio.

`irg_generacion_diplomados_website_verify` sustituye `action_reprint` sin
`super()`. El modulo nuevo debe depender de ese addon para ganar el MRO y
usar `_get_diplomado_pdf_data()`.

## Motivos

- En lotes de diplomado, `start_date` y `date_start_class` a menudo no coinciden.
- Regenerar en cada GET rompe suites `post_install` de
  `irg_diplomado_portal_request` e `irg_campus_diplomados_portal`.
- Los diplomas reales siempre guardan `start_date`; al cambiar la fecha de
  inicio de clases del lote, la siguiente descarga del alumno actualiza el PDF.

## Gotchas

- No modificar `irg_generacion_diplomados`; heredar.
- Renderizar el PDF antes de escribir `start_date` y el adjunto. Si ReportLab
  falla, el PDF anterior y la fecha guardada quedan como estaban.
- Sobrescribir `attachment_id.datas` solo si `res_model` y `res_id` apuntan a
  este registro. Si el adjunto es ajeno, crear uno nuevo; no hacer `unlink()`.
- En descarga campus, comprobar partner y nota > 7.0 **antes** de
  `action_reprint`. Republicar rutas con `@http.route()` vacio.
- `'app.gradebook.student' in self.env`, no `env.get`.
- `auto_install` en False: instalar el modulo de forma explicita por entorno.
