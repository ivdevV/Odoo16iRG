# Changelog — gradebook-auto-close

## 2026-07-15

### Added

- Nuevo addon Odoo 16 `irg_gradebook_auto_close`, dependiente de
  `isep_gradebook` y sin modificación de módulos existentes.
- Condición de elegibilidad por libreta y línea para notas finales, exámenes y
  asignaciones aplicables.
- Autocierre posterior a `create`, `write` y `unlink` de resultados, incluyendo
  cambios de relación, operaciones multi-registro y reapertura seguida de una nueva
  operación de nota.
- Suite de 13 tests post-install y documentación funcional, técnica y reusable.

### Fixed

- Preservación de las libretas anterior y nueva cuando un resultado cambia de línea.
- Compatibilidad con el override base singleton durante writes multi-registro.
- Diferimiento del autocierre durante writes internos de `scoring_total` originados
  por un create por lotes con redondeo; reevaluación única al final y rebrowse en
  contexto normal.
- Captura limitada de `UserError` del cierre estándar para no abortar el guardado
  cuando faltan evaluaciones requeridas por el template.

### Tested

- Upgrade fresco en `test_irg_db` mediante `docker-compose.local.yml`.
- 13 tests post-install: 0 fallos, 0 errores.
- Compilación Python 7/7, manifest, imports, patrones prohibidos y alcance del diff.
- Sin cambios en `isep_gradebook`; revisiones anti-patrones y calidad en estado
  `LISTO`, sin hallazgos pendientes.

No se realizó commit, pull, push ni despliegue remoto como parte de esta misión.
