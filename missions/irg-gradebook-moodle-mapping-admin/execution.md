# Execution log — irg-gradebook-moodle-mapping-admin

- 2026-07-22: misión full/tier complex iniciada desde la especificación aprobada.
- Runtime: docker-compose.local.yml; DB: test_irg_db.
- Se preservan irg_gradebook_moodle_wizard e irg_gradebook_moodle_routing.
- Diseño/plan no autorizan commit, push, despliegue ni importación real.
- 2026-07-22: Security Advisor emitió `[NO]` porque el límite se aplicaba tras
  `b64decode`; Task 2 permaneció bloqueada.
- 2026-07-22: diseño, plan de implementación y plan de misión enmendados con
  límite base64 previo, control en `create`/`write`, pruebas RPC y lectura shell
  absoluta/acotada. Solicitada nueva revisión independiente.
- 2026-07-22: Security Advisor revalidó la enmienda y emitió `[YES]`; queda
  abierto el gate para iniciar Task 2 con TDD.
- 2026-07-22: baseline de runtime resuelto con el compose base `/Users/ivrogo/Workspace/Proyectos iRG/Odoo16iRG/docker-compose.local.yml` y el overlay `.superpowers/sdd/docker-compose.worktree.yml`, que monta este worktree en lugar de `/mnt/extra-addons`.
- Servicios confirmados: `pgodoo_local`, `redisodoo_local`, `odoo_local`.
- Regresión baseline de `irg_gradebook_moodle_routing`: 20 métodos, 22 pruebas, 0 fallos y 0 errores.
- 2026-07-22: Task 4 descubrió que las operaciones no transportaban nombre de
  curso ni nombre/código de asignatura del CSV, impidiendo la revalidación
  completa. El usuario autorizó ampliar `ImportPlan`; diseño, plan y misión se
  enmendaron y se solicitó nueva revisión de seguridad.
- 2026-07-22: Security Advisor aprobó la ampliación de `ImportPlan` con un
  tercer dictamen `[YES]`; Task 4 puede reanudarse con TDD.
- 2026-07-22: Review de Task 4 pidió bloquear mezcla de padres y planes manuales
  no canónicos. Se añadieron al diseño/plan `conflicting_subject_parent` y una
  prevalidación completa antes de cualquier escritura; solicitada revisión de
  seguridad.
- 2026-07-22: Security Advisor aprobó esos controles con un cuarto `[YES]`;
  Task 4 volvió a Implementación para corregir y revalidar.
- 2026-07-22: Task 2 RED ejecutado con el compose base y overlay de worktree;
  `TestMappingAdminModels.test_course_and_subject_context_fields` falló como
  se esperaba por ausencia de `irg_op_course_database_id` (exit 1). Evidencia:
  `artifacts/red-tests.txt`.
- 2026-07-22: Task 2 GREEN ejecutado tras importar la extensión de modelos;
  instalación satisfactoria y `TestMappingAdminModels` con 0 fallos y 0 errores
  (exit 0). Evidencia: `artifacts/green-tests.txt`.
- 2026-07-22: Task 3 RED ejecutado antes de crear el servicio; la carga falló
  por ausencia esperada de `services.mapping_import` (exit 255). Evidencia:
  `artifacts/red-tests.txt`.
- 2026-07-22: Task 3 GREEN implementó análisis CSV binario acotado y de solo
  lectura. La suite dirigida pasó 8 métodos y la regresión conjunta Task 2+3
  pasó 9 métodos, ambas con 0 fallos y 0 errores. Evidencia:
  `artifacts/green-tests.txt`.
- 2026-07-22: Task 4 RED inicial ejecutado antes de implementar apply; los 5
  métodos fallaron por ausencia esperada de `apply_plan`/`_upsert_activities`.
- 2026-07-22: Task 4 implementó upsert conservador con búsquedas
  `active_test=False`, reactivación, claves SQL existentes, preservación de
  tipos/líneas históricas y propagación de errores ORM sin commit ni borrado.
- 2026-07-22: la suite inicial de apply pasó 5 métodos y la regresión conjunta
  pasó 35 métodos, sin fallos ni errores.
- 2026-07-22: tras la enmienda aprobada y el tercer `[YES]` del Security
  Advisor, se añadió un segundo RED: 8 métodos fallaron por ausencia de
  `op_course_name`, `op_subject_name` y `op_subject_code` en los transportes.
- 2026-07-22: análisis y operaciones conservan los testigos fuente; apply
  compara normalizadamente nombre de curso, nombre y código de asignatura
  inmediatamente antes de los upserts. Los tres cambios concurrentes producen
  `ValidationError` y rollback sin escrituras supervivientes.
- 2026-07-22: GREEN final dirigido pasó 8 métodos/10 pruebas Odoo; regresión
  Tasks 2–4 + routing pasó 38 métodos (24 pruebas Odoo del addon admin y 22 de
  routing), con 0 fallos y 0 errores. Sintaxis, whitespace y controles estáticos
  de operaciones prohibidas pasaron. Evidencia: `artifacts/red-tests.txt` y
  `artifacts/green-tests.txt`.
- 2026-07-22: RED independiente del conflicto de padre falló 1/1 porque la
  segunda fila reemplazaba el `op_course_id` de la primera; RED independiente
  de preflight terminó con 15 fallos y 1 error en 14 métodos, incluyendo el
  `AttributeError` esperado para un miembro de asignatura malformado.
- 2026-07-22: el análisis conserva la primera operación de asignatura y omite
  cualquier fila posterior con la misma clave asignatura/Moodle y otro curso,
  contabilizando `conflicting_subject_parent` sin mezclar actividades.
- 2026-07-22: `apply_plan` ejecuta un preflight puramente estructural completo
  antes de revalidar ORM o crear contadores: raíz/contenedores/miembros, tipos e
  IDs, claves únicas, padre y metadatos normalizados, actividades no vacías y
  IDs de actividad únicos. Los errores se convierten en `ValidationError`
  sanitizado y no alcanzan ninguna llamada de upsert.
- 2026-07-22: GREEN dirigido pasó el conflicto 1/1 y apply 14/14; regresión
  Tasks 2–4 + routing pasó 45 métodos (31 pruebas Odoo del addon admin y 22 de
  routing), con 0 fallos y 0 errores. Evidencia actualizada en
  `artifacts/red-tests.txt` y `artifacts/green-tests.txt`.
- 2026-07-22: revisión estática detectó evaluación ansiosa de `.strip()` sobre
  metadatos escalares no-string. Se añadieron casos RED separados (2 errores
  `AttributeError`) y se sustituyó el `all(...)` por condiciones `or` con
  cortocircuito tras las comprobaciones de tipo.
- 2026-07-22: GREEN escalar pasó 1/1 y la regresión final se repitió tras la
  corrección: 45 métodos, 31 pruebas admin y 22 routing, 0 fallos/errores.
- 2026-07-22: refactor GREEN dividió el preflight en helpers acotados para plan,
  curso y asignatura/actividades. La regresión final posterior volvió a pasar
  45/45; AST/sintaxis, whitespace, operaciones prohibidas, `git diff --check`
  y estado Git quedaron comprobados. No se hizo stage, commit ni push.
- 2026-07-22: Task 5 empezó con pruebas RED de permisos, estados, singleton,
  límites base64 antes/después de decodificar, RPC `create`/`write`, análisis
  sin escrituras, reset por cambio, reanálisis al confirmar, resultados y
  vistas/ACL. RED falló por ausencia esperada del modelo transient.
- 2026-07-22: implementado el wizard exclusivamente administrativo con límite
  previo `MAX_BASE64_SIZE`, límite posterior de 10 MiB, tipos estrictos,
  estado y resultados propiedad del servidor, cuatro acciones con permisos,
  singleton y estado, reanálisis de bytes persistidos al confirmar y
  `Command.set` limitado a los Many2many del transient.
- 2026-07-22: el primer intento GREEN localizó un nombre automático de tabla
  Many2many superior al límite PostgreSQL; se corrigieron ambas relaciones con
  nombres explícitos cortos. El upgrade y la suite dirigida pasaron después
  10/10 sin fallos ni errores.
- 2026-07-22: añadidas ACL CRUD, action y menú solo para `base.group_system`,
  formulario con statusbar/botones por estado y herencias precisas de las
  cuatro vistas de routing. Las tablas muestran contexto de curso/Moodle,
  IDs/nombre/código de asignatura, conteo y lista de actividades.
- 2026-07-22: corregido el minor aprobado de Task 2: `irg_activity_count` usa
  `N.º de actividades`; una prueba comprueba que ya no duplica la etiqueta de
  `line_ids` (`Actividades`).
- 2026-07-22: regresión final Tasks 2–5 + routing pasó 55/55 métodos (43 tests
  Odoo del addon admin y 22 de routing), XML 2/2, compileall, AST, longitud,
  whitespace y controles estáticos. No se hizo stage, commit, push ni PR.
- 2026-07-22: la Review menor se verificó contra el código: el snapshot de
  Validar solo comparaba conteos y el resumen/error exponía claves y frases
  internas inglesas. Se escribieron primero pruebas de snapshot persistente,
  rutas apply/upsert no invocadas, etiquetas españolas y errores saneados.
- 2026-07-22: RED focal produjo los dos fallos esperados por `blank_row` y
  `CSV courses: missing required header(s)`. Tras el primer GREEN, un RED de
  privacidad adicional demostró que el texto fuente seguía en `__cause__`.
- 2026-07-22: implementado un mapa cerrado para las trece razones del servicio,
  un mapa cerrado para sus ocho errores de fichero y fallbacks genéricos sin
  interpolar contenido. Los `ValidationError` de servicio usan `from None` para
  que la causa original no se exponga en la cadena de error.
- 2026-07-22: GREEN focal pasó 3/3 y privacidad 1/1. Regresión completa final
  Tasks 2–5 + routing pasó 57/57 métodos (45 tests Odoo admin + 22 routing),
  sin fallos ni errores. No se hizo stage, commit, push ni PR.
- 2026-07-22: Task 6 empezó con pruebas de equivalencia binario/ruta, rechazo
  de rutas relativas y lectura acotada. El RED terminó con exit 255 por la
  ausencia esperada del paquete `tools` antes de crear producción.
- 2026-07-22: añadido el adaptador de shell. Exige rutas absolutas, abre cada
  fichero una sola vez y lee como máximo `MAX_FILE_SIZE + 1`; delega análisis y
  aplicación al servicio común sin ejecutar commit, unlink ni sudo.
- 2026-07-22: GREEN focal de análisis pasó 12 métodos/14 pruebas Odoo. La
  regresión completa Tasks 2–6 + routing pasó 59 métodos (47 tests admin + 22
  routing), con 0 fallos y 0 errores.
- 2026-07-22: documentada la jerarquía, UI, contrato CSV, motivos, cabeceras
  legadas, shell, límites, permisos y rollback. El primer formato Markdown
  generó avisos de docutils durante el upgrade; se convirtió a sintaxis RST
  compatible y el upgrade posterior terminó sin diagnósticos del README.
- 2026-07-22: smoke real de solo lectura ejecutado con Downloads montado `:ro`.
  Los tres modelos persistentes permanecieron 0→0 y no se llamó apply. La DB de
  prueba carece de los 28 cursos Odoo fuente: 0 operaciones de curso/asignatura,
  con descartes agregados `missing_odoo_record=28`, `blank_row=41`,
  `invalid_id=83` y `missing_course_pair=286`. Evidencia:
  `artifacts/real-csv-smoke.txt`.
- 2026-07-22: compileall, AST (16 archivos), longitud, whitespace y scans
  estáticos del adaptador pasaron. No se hizo stage, commit, push, despliegue
  ni importación real.
- 2026-07-22: la revisión integral final bloqueó el gate con tres hallazgos
  importantes: parser CSV no estricto ante comillas sin cerrar,
  previsualización sin conteos de creación/actualización y ausencia de
  `active` en la tabla plana de asignaturas. Validación no comenzó y la fase
  de Implementación/TDD se reabrió. Evidencia: `artifacts/review.txt`.
- 2026-07-22: RED focal de los tres bloqueos terminó con 3 fallos y 1 error
  en 4 métodos: el CSV truncado no fallaba, el resumen no tenía preview, el
  wizard no lo mostraba y la vista plana no incluía `active`.
- 2026-07-22: el lector usa `strict=True`; cualquier `csv.Error` bloquea el
  análisis completo con un `ValueError` fijo y saneable antes de analizar filas.
- 2026-07-22: `analyze_bytes` calcula sin escrituras los conteos de curso,
  asignatura y actividad. Preview y apply comparten los mismos helpers de
  búsqueda con `active_test=False`; una actividad existente solo cuenta como
  actualizada cuando el nombre entrante no vacío provocaría `write`.
- 2026-07-22: `action_validate` muestra los tres conteos en futuro y español;
  la tabla plana de asignaturas muestra `active`. El snapshot prueba que ni
  registros inactivos ni metadatos de escritura cambian durante el análisis.
- 2026-07-22: GREEN focal pasó 4/4; regresión completa pasó 61 métodos
  (49 admin + 22 routing), 0 fallos/errores. AST 16/16, XML 2/2, compileall,
  longitud, whitespace y `git diff --check` pasaron. Sin stage, commit o push.
- 2026-07-22: validación independiente final ejecutó desde cero compileall
  (caché en `/tmp` por montaje read-only), manifest AST, XML 2/2 y upgrade más
  suite completa en one-off con compose base+overlay y `--no-http`: 61 tests,
  0 fallos y 0 errores (49 admin + 22 routing).
- 2026-07-22: smoke UI/server reversible validó las cuatro vistas combinadas,
  ACL/action/menu solo sistema y denegación a un usuario interno sintético.
  El administrador creó el wizard con copias base64 de ambos CSV reales y
  ejecutó solo `action_validate`; `action_apply` tuvo 0 llamadas y los tres
  modelos persistentes conservaron snapshots idénticos. La ausencia de master
  data produjo preview 0 con conteos agregados registrados sin PII.
- 2026-07-22: rollback explícito eliminó transient y fixture; no quedó ningún
one-off vivo y el servicio principal siguió montando el checkout principal
read-only. `verification.json` quedó `passed`. No se hizo stage, commit, push,
despliegue, importación ni apply real.
- 2026-07-22: cierre documental posterior a Review y Validación aprobadas:
  README actualizado con preview de create/update sin escrituras, parser CSV
  estricto, paridad UI/shell y limitación del smoke por ausencia de maestro;
  creado CHANGELOG de misión y actualizada la knowledge reutilizable para el
  flujo actual de dos CSV consolidados. Se comprobaron formato RST/Markdown,
  enlaces internos, coherencia y alcance exclusivamente documental. No se
  modificaron código, pruebas, permisos, XML, manifest ni configuración; no se
  reabrieron Review ni Validación.
- 2026-07-22: la comprobación final acotada confirmó `verification.json` en
  `passed`, `git diff --check`, scope Git sin stage y runtime principal
  restaurado; se retiraron únicamente cachés Python generadas
  (`__pycache__`/`.pyc`) del addon nuevo.
