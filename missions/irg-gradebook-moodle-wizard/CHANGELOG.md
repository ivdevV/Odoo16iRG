# Changelog de misión

## 2026-07-21 — `16.0.1.0.0`

### Añadido

- Addon puente `irg_gradebook_moodle_wizard`, sin cambios en módulos
  existentes.
- Mapeo propio de asignatura, curso y actividades Moodle, con ACL y
  constraints de integridad.
- Servicio de `grade items` con validación estricta del esquema devuelto por
  Moodle y errores funcionales seguros.
- Wizard individual editable con matching por `md_id`, email y nombre
  normalizado.
- Conversión a la escala de la libreta, media por asignatura y tipo, y upsert
  de resultados marcados con `is_moodle`.
- Importador idempotente y atómico del CSV `MAP_ASIGNATURAS`.
- Suite TDD de 44 métodos, incluidos escenarios de seguridad, integridad,
  concurrencia e importación.

### Decisiones funcionales

- Se conserva una única línea agregada por asignatura y tipo.
- `quiz` se mapea a `exam` y `assign` a `assignment`.
- Un template con `qty != 1` o una nota manual del mismo tipo marca la línea
  como incompatible; no se modifican los computes base de `isep_gradebook`.
- Una resincronización actualiza la fila Moodle existente y no crea
  duplicados.

### Seguridad e integridad

- Acceso al wizard limitado a Faculty y Gradebook Admin, con guards
  server-side y bloqueo de libretas finalizadas.
- Clave única nullable `moodle_sync_key`, locks ordenados y revalidación tras
  lock para serializar aplicaciones concurrentes.
- Rechazo de mapas ambiguos, colisiones `id`/`cmid`, tipos inconsistentes,
  notas no finitas o fuera de escala e IDs CSV inválidos.

### Validación

- Review independiente final sin observaciones abiertas.
- Upgrade y suite Odoo: 44/44 métodos, 50 tests/subtests, 0 fallos y 0 errores.
- Smoke UI end-to-end satisfactorio contra un Moodle local simulado; promedio
  `0 → 8` y segunda sincronización con una sola fila persistida.
- Import local de las 369 filas reales: todas omitidas porque `test_irg_db`
  no contiene `op.subject`; rollback y cero residuos.

### Limitaciones verificadas

- El smoke contra un WS Moodle real quedó `skipped`: 101 bases locales
  inspeccionadas y ninguna credencial disponible. La semántica real de los
  IDs del Excel (`id` o `cmid`) queda pendiente de comprobar en un entorno con
  credenciales; el addon soporta ambos y rechaza colisiones.
- La hoja importada contiene quizzes; las tareas están soportadas, pero no hay
  datos `assign` en el import inicial.
