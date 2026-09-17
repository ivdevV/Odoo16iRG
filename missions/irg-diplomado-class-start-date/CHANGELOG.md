# Changelog — irg-diplomado-class-start-date

## 16.0.1.0.0

- Nuevo modulo `irg_generacion_diplomados_class_start_date`.
- El texto «celebrado del …» usa `date_start_class` del lote (fallback
  `start_date`).
- Reimprimir regenera el PDF. La descarga de portal lo regenera si la fecha
  guardada esta desfasada respecto al lote.
- No se tocan diplomas de graduacion ni la fecha de fin o de expedicion.
