# Changelog — fix-gradebook-homeclass-edition-fallback

## 2026-07-23

- Añadido el addon puente `irg_gradebook_moodle_homeclass_editions` para
  resolver varias ediciones HomeClass activas por asignatura.
- Se prioriza la edición cuyo año inicial coincide con el lote, se admite un
  mapa genérico y se usa el resto solo como respaldo determinista.
- El fallback se limita a ausencia de actividad, alumno o nota utilizable; las
  colisiones estructurales quedan como incompatibilidades bloqueantes.
- Incorporada detección de periodos `AAAA-AAAA`, `AAAA_AAAA` y `AAAA/AAAA`,
  con override manual de la edición HomeClass.
- Documentado que el flujo Online conserva el comportamiento existente.
