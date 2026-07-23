# Changelog

## 2026-07-22 — iRG Gradebook Moodle Routing 16.0.1.0.0

- Añadido el modelo padre `irg.gradebook.moodle.course.map` para relacionar el
  curso Odoo con el ID y nombre del curso Moodle, su modalidad, edición y
  estado.
- Añadido routing estricto por lote: `HC` selecciona HomeClass y `ONL`
  prioriza la edición del año del lote con fallback genérico inequívoco.
- Limitados los mapas de asignatura y Activity IDs al mapa de curso padre
  resuelto antes de contactar Moodle.
- Añadidas constraints de ID positivo, unicidad e integridad recíproca entre
  curso padre, Moodle Course ID y pertenencia de la asignatura al curso Odoo.
- Añadidas ACL de lectura para usuarios internos y administración exclusiva
  para `base.group_system`, además de vistas de cursos y del padre en mapas de
  asignatura.
- Añadido importador idempotente de los tres CSV MacRoman, con validación de
  headers e IDs, estadísticas de descartes, upsert de mapas y Activity IDs, y
  conservación de datos históricos sin borrados ni desactivaciones.
- Endurecida la clasificación Online: solo `"(ONLINE)"` y
  `"(ONLINE AAAA)"` exactos son seleccionables; los marcadores malformados se
  rechazan como `invalid_online_marker` antes de tocar el ORM o Moodle.
- Añadida documentación operativa compatible con el parser reStructuredText
  usado por Odoo para la descripción del addon.
