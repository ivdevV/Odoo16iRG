# Ejecución

## Estado inicial

- Diagnóstico reproducido contra Moodle beta con el curso 35 y el alumno de la
  libreta AD000084.
- Evidencia representativa: el CSV contiene `205`; Moodle devuelve
  `id=555`, `cmid=3290`, `iteminstance=205`, `itemmodule=quiz`.
- El addon de ediciones HomeClass ya consulta los cursos 35 y 36.
- No se han realizado cambios funcionales, commits ni publicaciones.
- El intento inicial de línea base incluyó la suite interna
  `irg_gradebook_moodle_wizard` bajo extensiones ya instaladas y produjo 21
  errores de aislamiento conocidos. Se corrigió el comando al gate usado y
  aprobado en la misión HomeClass anterior: routing, mapping admin y
  HomeClass.
- Línea base canónica: 67 pruebas, 0 fallos y 0 errores.
- TDD RED del resolvedor: 3 métodos, 3 errores esperados por ausencia de
  `_irg_match_grade_items`; evidencia en `artifacts/red-tests.txt`.
- TDD RED del esquema: el payload con `iteminstance="205"` fue aceptado y la
  prueba falló porque no se lanzó `UserError`.
- TDD RED de agregación/HomeClass: nota por `iteminstance`, diagnóstico de
  ausencia, colisión entre namespaces y conflicto de tipo fallaron como se
  esperaba.
- GREEN dirigido: 21 métodos del addon nuevo, 0 fallos y 0 errores.
- Regresión conjunta: 94 métodos, 0 fallos y 0 errores.
- `compileall` del addon nuevo: correcto.
- Review independiente: **Approved**, sin hallazgos Critical, Important ni
  Minor.
- Validación independiente: `verification.json` en estado `passed`; 94
  métodos, 0 fallos y 0 errores; base temporal eliminada y servicio compartido
  restaurado.
- Documentación añadida: README del addon, changelog de misión y conocimiento
  reutilizable sobre los tres namespaces de IDs Moodle. No se modificó código
  ni runtime durante esta fase.
- Comprobación final acotada: README RST parseado con docutils, documentos sin
  placeholders ni defectos de whitespace, bases TDD/baseline eliminadas, cero
  contenedores one-off y servicio principal montado al checkout original.
