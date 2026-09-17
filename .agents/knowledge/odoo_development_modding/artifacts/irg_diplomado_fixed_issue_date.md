# Patron: Fecha fija 26 de septiembre en diplomados

Fecha: 2026-08-31

Modulo: `irg_generacion_diplomados_fixed_issue_date`

## Decision reutilizable

La linea «Barcelona, a …» de un diploma de diplomado no debe usar el dia de
impresion. Dia y mes son siempre 26 de septiembre; el año es el de
`fields.Date.context_today` al generar.

La fuente unica es `irg.diplomado.registry._irg_fixed_issue_date()`. El wizard
fuerza el valor en `create`/`write` porque
`irg_generacion_diplomados_website_verify` sustituye `action_print_diplomado`
sin llamar a `super()`. El portal no envia `issue_date`; el default del
registro cubre esa ruta.

## Gotchas

- No modificar `irg_generacion_diplomados`; heredar.
- No forzar `issue_date` en `registry.create()`: romperia tests y registros
  historicos que pasan una fecha explicita.
- `auto_install` en False: instalar el modulo de forma explicita por entorno.
