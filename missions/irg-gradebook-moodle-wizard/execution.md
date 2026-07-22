# Diario de ejecución — Wizard Moodle para la libreta

## Apertura

- Fecha: 2026-07-21.
- Nivel/tier: `full` / `complex`.
- Worktree: `/Users/ivrogo/.codex/worktrees/Odoo16iRG/gradebook-moodle-wizard`.
- Rama: `feat/gradebook-moodle-wizard`.
- Base: `ba75954925d5ea164d5e2234e7eaf2044d4ce7cf` (`origin/Dev_iRG` actualizado).
- Estado inicial del worktree: limpio.
- El checkout principal tenía cambios previos del usuario; quedan fuera de alcance y no se modifican.

## Decisiones previas

- El usuario autorizó adelantar Task 7 para cumplir RED antes de código de producción.
- Se usa worktree aislado y overlay de Docker conforme a la política del repositorio.
- El plan se ejecutará mediante codificadores por task, review independiente por versión funcional y validación independiente final.

## Registro

| Comando/acción | Resultado | Detalle |
| --- | --- | --- |
| `git fetch origin Dev_iRG` | pass | Base remota actualizada. |
| `git worktree add ... -b feat/gradebook-moodle-wizard origin/Dev_iRG` | pass | Worktree limpio y aislado. |
| Consulta knowledge/workflow | pass | Reglas de módulo nuevo, herencia, ACL y runtime incorporadas al plan de misión. |
| Baseline `-u isep_gradebook,irg_moodle_grades_sync` con overlay | pass | Registry actualizado; aviso preexistente por `irg_gradebook_partial_averages` ausente, sin traceback ni exit no-cero. |

## Task 1 — scaffold

- Codificador independiente creó exactamente los cinco archivos del scaffold.
- Checks: `py_compile`, AST del manifest, `git diff --check` y alcance, todos pass.
- Commit: `cfa660d292a521317deef0ad0b097dd2007787a7`.
- Review independiente: spec compliant, sin findings, Task quality Approved.

## TDD RED adelantado — Task 7

- Se escribieron los siete escenarios finales antes de cualquier modelo o lógica productiva.
- Se añadieron placeholders estrictamente sintácticos para que Odoo cargase el addon incompleto.
- RED: 7 tests, 1 fallo de aserción esperado por cuatro modelos ausentes, 6 skips y 0 errors.
- Evidencia: `artifacts/red-tests.txt`.
- Commit: `5b90360a6` (`test(gradebook): suite del wizard de sincronización Moodle`).
- Review independiente: spec compliant, sin findings, Task quality Approved.
- Avisos preexistentes del entorno: columna `username` NOT NULL y estado inconsistente del addon local ausente `irg_gradebook_partial_averages`; ninguno produjo error en la suite del addon nuevo.

## Task 2 — mapeo de actividades

- Implementados `irg.gradebook.moodle.map` y `.line`, constraint, ACL, vistas y acción.
- La nota del plan se resolvió con el XML id real `isep_gradebook.menu_app_gradebook_root`.
- Instalación diferida objetivamente hasta registrar los transient models de Task 5.
- Checks Python/XML/CSV/manifest/diff: pass.
- Commit `fc9759325`; Review independiente spec compliant y Task quality Approved, sin findings.

## Task 3 — origen Moodle y apertura

- Añadido `is_moodle` mediante `_inherit` y la acción singleton de apertura/carga del wizard.
- No se añadió el override opcional de `compute_name`: no existe todavía evidencia de fallo que lo justifique.
- Checks Python/AST/diff/alcance: pass; instalación diferida hasta Task 5.
- Commit `669543b1b`; Review independiente Approved, sin findings.

## Task 4 — servicio de grade items

- Implementada la subclase mínima y su contrato de retorno/error exacto.
- Checks estáticos/imports/contrato/diff: pass; ejecución integrada diferida a Task 5.
- Commit `490f09e82`; Review independiente Approved.
- Minor P3 registrado para final review: `logging` y `_logger` están declarados pero no usados, tal como aparece en el snippet del plan.

## Task 5 — wizard, hardening y GREEN

- GREEN nominal inicial: 7/7 tests, sin necesidad de override de `compute_name`.
- La Review detectó incompatibilidad entre una línea agregada y templates `qty != 1`; el usuario eligió preservar los computes base y bloquear por línea los casos incompatibles.
- Security Advisor: primer diseño `[NO]` por snapshot `REPEATABLE READ`; diseño enmendado `[YES]` con clave Moodle única nullable, locks ordenados, versionado de padres y guardas server-side.
- Se añadieron incompatibilidad por template/manual, escala finita, ambigüedad de mapa e ID/cmid, ACL faculty/admin, pertenencia/estado, clave única, serialización/retry y hooks concurrentes de líneas.
- Orden global de locks aprobado: wizard padre → líneas transient → asignaturas.
- GREEN final: 24/24 tests, incluido `SerializationFailure` real, retry y una sola fila; cleanup 0.
- Commits funcionales: `3d2738e42`, `25e74799c`, `a8cafbb2a`, `16477a074`, `a5212bc90`.
- Review independiente final: Approved, sin Critical/Important/Minor.

## Smoke WS previo a vistas

- El Excel se leyó sin modificar mediante `@oai/artifact-tool`: `MAP_ASIGNATURAS` contiene 370 filas y 11 columnas; el primer curso es Moodle 44 y los IDs iniciales son 395 y 397.
- El smoke real en `test_irg_db` devolvió `SMOKE_WS no_credentials`.
- Se comprobaron todas las bases locales: ninguna contiene registros en `moodle.credentials`.
- La semántica real `id` frente a `cmid` queda objetivamente no verificable en local; el código conserva resolución de ambos namespaces y rechaza colisiones.

## Task 6 — vistas e instalación

- Vistas de wizard y botón instaladas; estado `incompatible` visible y no editable.
- Botón limitado visualmente a Faculty/Gradebook Admin, coherente con ACL y guards.
- Upgrade completo con overlay: 24 tests, 0 failures, 0 errors.
- Commit `4bc02b6e1`; Review aceptada.
- Minor pendiente de final review: ocultar/rechazar apertura temprana cuando la libreta ya está `done`.

## Task 7 — suite

- Los siete escenarios originales se escribieron en RED antes de producción.
- La suite creció por findings TDD de Review/Security hasta 24 escenarios.
- Último GREEN integrado en Task 6: 24/24.

## Task 8 — importador del mapeo

- CSV extraído del Excel original mediante `@oai/artifact-tool`, sin modificar el libro.
- TDD añadió cobertura de create/update idempotente, regeneración, skips, preservación ante filas inválidas, overflow, positividad y rango PostgreSQL.
- GREEN final: 29/29 tests.
- Import real completo: 369 filas skipped por ausencia de asignaturas locales, 0 traceback, rollback y 0 mapas residuales.
- Commits `b21c1fa69`, `9775d2204`, `86c3b22d1`.
- Review independiente final: Approved, sin findings.

## Task 6 — vistas del wizard y acceso desde la libreta

- TDD no es viable para este cambio aislado: los dos artefactos son XML declarativo de `ir.ui.view`, sin lógica productiva nueva y sin API Python adicional. El contrato verificable es la compilación XML, la carga de vistas/ACL y la suite integrada de Odoo tras el upgrade.
- Se mantiene el diseño ya aprobado en `docs/superpowers/plans/2026-07-21-irg-gradebook-moodle-wizard.md`: formulario modal del wizard, árbol no creable/borrable, estados visuales y botón heredado en el `header` de la libreta individual.
- Implementación: los dos placeholders se sustituyeron sin modificar addons existentes. La línea `incompatible` se decora con warning; `alumno_no_encontrado`, con danger. El botón incluye ambos grupos autorizados por el guard server-side.
- Upgrade con overlay: `-u irg_gradebook_moodle_wizard --test-enable --stop-after-init --log-level=test` terminó con exit 0; resumen Odoo `0 failed, 0 error(s) of 24 tests`.
- Checks: XML, AST manifest, CSV ACL 9x8, IDs/vista/ACL en `test_irg_db` y `git diff --check`, todos pass. La evidencia concisa está en `artifacts/task6-install-tests.txt`.
- Limpieza: no quedaron contenedores temporales y el servicio persistente conserva el mount del checkout principal. El smoke WS no se reintentó; sigue bloqueado por `no_credentials` y ausencia global de `moodle.credentials` local.

## Task 8 — import del mapeo n8n

- Se añadió primero una regresión que carga el script por `importlib` desde su ruta y genera un CSV UTF-8 temporal con una `op.subject` real.
- El primer intento de RED no fue aceptado porque el fixture incumplía la constraint preexistente del 100 % en la libreta. Se corrigió únicamente el fixture y el RED válido terminó con 25 tests, 1 fallo esperado por script ausente y 0 errores.
- Se implementó literalmente `tools/import_map_csv.py` según el brief, sin fallback por código ni dependencia runtime externa.
- GREEN final: 25/25, 0 fallos y 0 errores. La regresión prueba create, update idempotente sin duplicado, regeneración de líneas/IDs/nombres, tipo `quiz` y skip de asignatura ausente.
- El CSV real exportado se montó read-only solo en el overlay y se ejecutó mediante `odoo shell` en `test_irg_db`: 0 subjects, 0 creados, 0 actualizados y 369 saltados, sin traceback.
- Se hizo rollback explícito; los mapas eran 0 antes del import, antes del rollback y después del rollback. No quedaron contenedores temporales y el servicio persistente conserva el mount del checkout principal.
- Checks `py_compile`, AST, diff, alcance, ausencia del CSV en el addon y mounts: pass.
- Evidencia: `artifacts/task8-red.txt`, `artifacts/task8-green.txt` y `artifacts/task8-real-import.txt`.
- Commit funcional: `b21c1fa69` (`feat(gradebook): script de import del mapeo n8n a la tabla de mapeo`), limitado al script y sus tests TDD.

### Task 8 — corrección de findings de Review

- Root cause: la lista de actividades filtraba silenciosamente tokens inválidos y podía llegar al write con cero o solo parte de las líneas; la conversión de IDs no capturaba `OverflowError`.
- RED previo a producción: 27 tests, 3 fallos y 0 errores. Los fallos reprodujeron `abc`, `123,abc` y `inf`/overflow; también se incluyeron lista vacía, malformed, continuidad y counters.
- Fix mínimo: captura de `OverflowError` y validación atómica de tokens decimales positivos antes de construir vals y antes de `(5, 0, 0)`.
- GREEN final fresco: 27/27, 0 fallos y 0 errores.
- Import real repetido: 0 subjects, 369 skipped, 0 mapas antes/después del rollback y sin traceback.
- Checks py_compile/AST/diff/alcance/cleanup: pass.
- Commit de corrección: `9775d2204` (`fix(gradebook): validar filas del import Moodle`), limitado al script y sus tests.

### Task 8 — cierre P2 de límites Integer

- Root cause: la conversión float -> int truncaba valores fraccionarios y ningún tipo de ID aplicaba el máximo real de `fields.Integer`; un ID 2147483648 podía alcanzar PostgreSQL después del clear de líneas.
- RED: 29 tests, 2 fallos y 0 errores. Se cubrieron subject/course 0, negativos, sobre máximo y fraccionarios; Course ID 0/-1/2147483648; y activity IDs 0/-1/2147483648.
- Fix mínimo: constantes 1..2147483647 y guards previos a ORM/vals para subject, course y todas las actividades, manteniendo la compatibilidad float -> int solo cuando el float es integral exacto.
- GREEN final fresco: 29/29, 0 fallos y 0 errores.
- Import real repetido: 369 skipped, sin traceback, rollback explícito y 0 mapas residuales.
- Checks py_compile/AST/diff/alcance/cleanup: pass.
- Commit P2: `86c3b22d1` (`fix(gradebook): acotar IDs del import Moodle`), limitado al script y sus tests.

## Cierre funcional, Review y Validación

- Los últimos fixes de Review quedaron en `94272f53d` y `a0757b59a`; este
  último valida de forma estricta el esquema anidado consumido de Moodle.
- El P3 de Task 4 se cerró eliminando `logging`/`_logger` sin uso; el minor de
  Task 6 se cerró ocultando el botón en estado `done` y manteniendo además el
  rechazo server-side de apertura y aplicación.
- Review independiente final de `a0757b59a69710d8f2427d580beeb676566001b4`:
  `Ready to merge: Yes`, sin observaciones Critical, Important ni Minor.
- Validación independiente final: `status: passed` en `verification.json`.
- Upgrade y suite fresca con `docker-compose.local.yml` y overlay del
  worktree: 44/44 métodos, 50 tests/subtests en estadísticas, 0 fallos y 0
  errores.
- Smoke UI end-to-end contra mock Moodle local: botón visible, wizard por
  `md_id`, una línea `exam` con nota 8 editable, promedio `0 → 8` y segunda
  sincronización sin duplicar. Evidencia: `artifacts/task9-ui-smoke.txt`.
- Smoke WS real: `skipped` con justificación. Se inspeccionaron 101 bases
  locales y no existe ninguna fila de credenciales Moodle; no fue posible
  comprobar con un endpoint real si los IDs del Excel son `id` o `cmid`.
- Cleanup: fixtures y credenciales temporales a cero, servidor y mock aislados
  detenidos, sin contenedores efímeros y con los servicios originales
  restaurados.

## Documentación

- Se añadió `addons-extra/extrairg/irg_gradebook_moodle_wizard/README.md` con
  instalación, configuración, uso, permisos, importación, pruebas y
  limitaciones.
- Se documentó la opción 1 elegida por el usuario: una línea agregada por
  asignatura y tipo; `qty != 1` o una línea manual del mismo tipo producen
  estado incompatible, sin alterar los computes base.
- Se actualizó el changelog de misión y el estado del plan fuente. La
  publicación sigue pendiente y conserva su autorización separada.
- Knowledge evaluada: no se crea una entrada nueva. La regla de agregación y
  las incompatibilidades son contrato específico de este addon; los patrones
  generales de libretas y computes ya están cubiertos por
  `.agents/knowledge/odoo_development_modding/artifacts/irg_gradebook_auto_close.md`.
- Autocheck documental: fences Markdown balanceados, sin trailing whitespace,
  enlaces relativos existentes, `verification.json` válido, exactamente dos
  steps pendientes justificados y `git diff --check` limpio. Resultado: pass.
