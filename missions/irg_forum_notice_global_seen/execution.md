# Execution journal — IRG Forum Notice Global Seen

## Mission opening

- Date: 2026-07-20
- Mission level/tier: `full` / `complex`
- Worktree: `/Users/ivrogo/.codex/worktrees/Odoo16iRG/irg-forum-notice-global-seen`
- Base commit: `ff32a4022fab7f16d621ed471729e1a3efc85c27`
- Isolated worktree status at opening: `## codex/irg-forum-notice-global-seen`
  (clean; no tracked or untracked changes).

Commands used to establish the base:

```text
git rev-parse HEAD
git status --short --branch
```

## Predating dirty tree in the main checkout — read-only

The main checkout was inspected read-only at the same base commit.  Its
pre-existing dirty paths are out of scope and must remain untouched:

```text
M  addons-extra/addons_uisep/isep_gradebook/models/app_gradebook.py
?? .obsidian/
?? addons-extra/extrairg/irg_gradebook_partial_averages/
?? docs/superpowers/plans/
?? docs/superpowers/specs/2026-07-20-irg-forum-notice-global-seen-design.md
?? graphify-out/
?? missions/fix-gradebook-template-zero-averages/
?? missions/fix-subject-precedence-shared-course/
```

Only the mission-owned, pre-existing untracked approved documents in the main
checkout were amended: `docs/superpowers/plans/2026-07-20-irg-forum-notice-global-seen.md`
and `docs/superpowers/specs/2026-07-20-irg-forum-notice-global-seen-design.md`.
All other pre-existing dirty paths remain untouched. The worktree contains only
mission artifacts; no functional addon code has been created or changed.

## Security gate

The first two independent Security Advisor reviews returned `[NO]` findings for
public RPC-callable services, unscoped legacy rows, and owner-row reassignment.
The third independent re-review examined the documented private service
methods, record rules, legacy CRUD guard, authorization order, and required
negative/positive tests. It returned `[YES]` in
`artifacts/security-advisor.txt`; the final line is the required
`[YES] Reason: ...` conclusion. The pre-implementation Security Advisor gate
is passed and Task 2 is unblocked.

## Commands and results

| Command | Result | Notes |
| --- | --- | --- |
| `git rev-parse HEAD` | pass | Base commit recorded above. |
| `git status --short --branch` | pass | Isolated worktree was clean at opening. |
| `git -C <main-checkout> status --short --branch` | pass | Predating dirty paths recorded read-only. |
| `test -f missions/irg_forum_notice_global_seen/plan.md` | pass | Mission plan exists. |
| `test -f missions/irg_forum_notice_global_seen/execution.md` | pass | Execution journal exists. |
| `tail -1 missions/irg_forum_notice_global_seen/artifacts/security-advisor.txt` | pass | Third independent re-review ends in `[YES] Reason: ...`; Task 2 is unblocked. |
| `git diff --check` | pass | No whitespace errors in tracked changes; untracked mission artifacts were separately self-reviewed. |
| `git status --short --branch` | pass | Scope contains only the untracked mission directory at this point. |

## Task 2 — Implementación/TDD

- Se consultaron el brief autoritativo, el plan, la skill TDD, la skill de
  desarrollo Odoo 16, el workflow y las entradas knowledge sobre modding y
  visibilidad de foros antes de editar código funcional.
- Se creó el scaffold importable y la suite de diez escenarios antes de código
  productivo. Para garantizar el RED limpio solicitado, el test de registro
  falla explícitamente y los escenarios dependientes del modelo se omiten solo
  mientras el modelo no está en el registry.
- El primer lanzamiento no alcanzó un RED funcional: el checkout exige
  `op.course.code` y el fixture del brief solo definía `name`. Se añadieron
  `SEEN-A` y `SEEN-B` antes de producción y se repitió.
- Overlay de misión:
  `missions/irg_forum_notice_global_seen/docker-compose.worktree.yml`; el
  `docker compose config` confirmó el bind read-only del `addons-extra` de este
  worktree en `/mnt/extra-addons`.
- RED válido con la suite completa: `1 failed, 0 errors`; nueve tests omitidos
  para evitar `KeyError`. Un run focalizado preservó el mensaje exacto:
  `AssertionError: False is not true : irg.forum.notice.global.seen is absent
  from the registry`. Evidencia: `artifacts/red-model.txt`.
- El runtime se ejecutó exclusivamente con `docker compose ... run --rm
  --no-deps odoo_local`; no se recreó ni repuntó el servicio compartido.
- Tras RED se implementó el modelo global mínimo con unicidad
  `(user_id, post_id)`, compatibilidad de lectura legacy sin `course_id`,
  creación idempotente protegida por savepoint y servicios privados con
  `sudo()` limitado al almacenamiento técnico.
- Se añadieron ACL global exclusiva de `base.group_system`, reglas legacy por
  propietario para internos/portal y allow-all de system, además de una
  extensión legacy que rechaza `create`, `write` y `unlink` salvo `env.su` o
  grupo system.
- GREEN fresco, tras eliminar y recrear exclusivamente la base aislada de la
  misión: 10 tests, 0 fallos y 0 errores. Incluye negativos internos/portal,
  reasignación de `user_id`, lecturas owner-scoped y positivos sudo/system.
  Evidencia: `artifacts/green-model.txt`.
- Checks estáticos del brief: `compileall` PASS; una sola ACL y grupo
  `base.group_system` PASS; orden exacto del manifest PASS; XML parse PASS.
  Los tres `__pycache__` generados por `compileall` se eliminaron.
- Self-review: API privada, dominios sin curso, constraint, ACL/rules, guards,
  alcance de `sudo()` y cobertura negativa/positiva conformes; no existe diff
  en addons previos. `git diff --check` y trailing whitespace PASS.
- El contenedor persistente `odoo16irg_local` sigue montando
  `/Users/ivrogo/Workspace/Proyectos iRG/Odoo16iRG/addons-extra`; el overlay
  efímero nunca repuntó ni recreó ese servicio.
- Al cierre de esta fase del codificador, el Review independiente quedaba
  pendiente del orquestador raíz; esta frase conserva ese estado histórico y
  no describe el gate final, que se aprobó posteriormente antes de Task 3.
- `commit skipped: not authorized`. Tampoco hubo staging, push ni PR.
- Reporte del codificador: `.superpowers/sdd/task-2-report.md`.

## Task 3 — Implementación/TDD de rutas

- Se leyó el brief autoritativo, el contrato de visibilidad de foros, las
  reglas de modding, el workflow Odoo 16 y las skills TDD/verificación antes de
  editar producción.
- El fixture HTTP del brief no era ejecutable literalmente porque
  `op.course.code` es obligatorio en este checkout. Se corrigió antes del RED
  con los códigos únicos `GS-HTTP-A` y `GS-HTTP-B`, y se registró la diferencia
  en la evidencia.
- RED válido antes de crear `controllers/`: 4 fallos, 0 errores. Fallaron las
  dos escrituras globales (ruta con curso y ruta sin `course_id`) y la
  supresión global en los dos descubrimientos heredados. Los negativos
  ORM/RPC preexistentes ya pasaban. Evidencia: `artifacts/red-controller.txt`.
- Después del RED se creó la extensión mínima del controlador, se importó
  después de `models` y se republicaron las cuatro rutas heredadas.
- El marcado valida usuario autenticado, identificador entero, existencia del
  post y `_is_visible_for_user(user)` antes de obtener el modelo seen con
  `sudo()` y escribir. Un post no se acepta solo porque exista.
- GREEN: 20 métodos de test (24 en la estadística interna de Odoo), 0 fallos y
  0 errores. Cubre las dos rutas de descubrimiento, las dos rutas de marcado,
  mismo post en dos cursos, usuarios interno/portal sin visibilidad, público,
  ids inválidos/inexistentes, fronteras ORM/RPC y controles sudo/system.
  Evidencia: `artifacts/green-controller.txt`.
- Los intentos genéricos a `_irg_is_seen` y `_irg_mark_seen` devolvieron error
  de método privado y no crearon ni modificaron filas. Cada denegación de
  estado legacy/global comprueba tanto recuentos por usuario como contenido de
  las filas antes/después.
- Self-review de autorización: las cuatro rutas están republicadas; el
  usuario público queda rechazado por `auth='user'` y además existe el guard
  explícito compartido; la visibilidad se ejecuta antes del sudo técnico; solo
  después se llama al servicio privado de escritura. Sin observaciones
  bloqueantes del codificador.
- Al cierre inicial de esta fase del codificador, el Review independiente
  quedaba pendiente del orquestador raíz; después se ejecutó, detectó el gap
  course-less descrito abajo y exigió su corrección TDD.
- El runtime se ejecutó únicamente mediante `docker compose ... run --rm
  --no-deps odoo_local` con el overlay de misión. No se usó `exec`, no se
  repuntó ni recreó el servicio compartido.
- `python3 -m py_compile` y `git diff --check`: PASS. Los `__pycache__`
  generados localmente se eliminaron al cerrar.
- `commit skipped: not authorized`. No hubo staging, push ni PR.
- Reporte del codificador: `.superpowers/sdd/task-3-report.md`.

### Task 3 — corrección del finding de Review

- Finding `Important`: el padre condicionaba `_is_seen()` a un `course_id`
  truthy en `_find_notice_for_user_global`; por tanto, un aviso de foro
  irrestricto podía repetirse para un usuario sin cursos efectivos.
- Se añadió primero
  `test_any_campus_suppresses_seen_post_without_course_context`. El caso usa un
  administrador sin cursos efectivos (bypass de visibilidad permitido), crea
  foro/post irrestrictos, demuestra que el post es el candidato visible antes
  de marcarlo y exige que desaparezca tras el marcado global.
- El primer lanzamiento no se contó como RED: el post de clase y el nuevo
  empataron en `create_date` y el padre eligió el fixture anterior. Se corrigió
  solo el fixture desactivando ese candidato. RED válido posterior: 1 fallo,
  0 errores; el post objetivo se devolvía de nuevo después de estar visto.
  Evidencia exacta añadida a `artifacts/red-controller.txt`.
- Producción mínima: `_find_notice_for_user_global` delega toda la búsqueda,
  selección y visibilidad a `super()`, y solo añade una comprobación global
  incondicional sobre el candidato devuelto, incluso si `course_id` es falso.
  No fue necesario duplicar lógica del padre ni tocar addons existentes.
- GREEN completo con el mismo comando del módulo: 21 métodos (25 en stats
  Odoo), 0 fallos, 0 errores; `py_compile` y `git diff --check` PASS. Evidencia
  actualizada en `artifacts/green-controller.txt`.
- No se usó `exec`, no se repuntó el servicio compartido y no hubo stage,
  commit, push ni PR.

## Task 4 — Implementación/TDD del frontend race-safe

- Se leyó el brief autoritativo, el plan, las reglas Odoo/knowledge/workflow y
  las skills TDD y de verificación antes de cambiar producción.
- Primero se añadió el escenario HTTP real
  `test_browser_dismiss_persists_before_next_poll`, incluido el hook obligatorio
  `data-notice-id` y la comprobación tras más de un intervalo de polling.
- El browser test no llegó a ejecutar JavaScript en esta imagen: el run completo
  informó `websocket-client module is not installed`; tras aportar esa
  dependencia solo en `/tmp` de otro contenedor efímero, informó
  `Chrome executable not found`. El runtime de navegador de la sesión tampoco
  expuso browsers controlables. Son skips objetivos de entorno, no fallos de
  aserciones de aplicación. Evidencia: `artifacts/red-frontend.txt`.
- Por indicación del orquestador se añadió, aún sin producción, un test focal de
  contrato que fija remove/add exactos, fichero de replacement, `data-notice-id`,
  supresión antes de await, mapa de petición única por aviso, tratamiento de
  `{ok: false}`, ausencia de requisito `course_id` y orden prevent/await/finally
  navigation. RED válido: `AssertionError: 0 != 1`, 1 fallo, 0 errores.
- Después del RED se creó el replacement JS del nuevo addon y se sustituyó el
  asset parent en el manifest exactamente una vez y antes del asset nuevo. No
  se eliminó ni duplicó el SCSS padre ni `forum_share_override.js`.
- El cierre y backdrop suprimen el id antes de esperar, comparten una sola
  Promise in-flight por aviso, esperan el intento de persistencia y solo retiran
  el wrapper en `finally`. “Ver aviso” hace `preventDefault`, espera la misma
  persistencia y navega en `finally`, incluso ante fallo. Un response ausente o
  con `ok` falso se trata como error y se registra con `console.warn`; el aviso
  queda suprimido únicamente por el `Set` de la sesión de página.
- GREEN focal: 1 método, 0 fallos y 0 errores. GREEN completo: 23 métodos
  ejecutados, 0 fallos y 0 errores; el único browser test quedó omitido por la
  dependencia ambiental exacta indicada. Evidencia: `artifacts/green-frontend.txt`.
- Resolución real `?debug=assets`: replacement 1, parent popup 0, share override
  1 y SCSS parent 1. Evidencia: `artifacts/frontend-assets.txt`.
- Checks estáticos: compile Python en memoria, literal manifest, sintaxis JS,
  `git diff --check`, alcance Git y ausencia de contenedores efímeros: PASS.
- El fixture manual de la alternativa browser se limpió de la BD aislada:
  1 usuario, 1 foro y 1 post eliminados; no había filas global/legacy asociadas.
- Todos los comandos Odoo usaron el overlay y `run --rm --no-deps`; nunca se usó
  `exec` ni se recreó/repuntó el servicio compartido.
- Al cierre de la fase del codificador, el Review independiente quedaba
  pendiente del orquestador raíz; se ejecutó y aprobó antes de la validación
  preliminar, con una nota Minor no bloqueante de hardening del test estático.
- `commit skipped: not authorized`; tampoco hubo stage, push ni PR.
- Reporte del codificador: `.superpowers/sdd/task-4-report.md`.

## Gate de Review independiente — aprobado antes de Validación

- Task 1 fue revisada por `/root/task1_review` usando
  `.superpowers/sdd/task-1-review.patch` y el reporte
  `.superpowers/sdd/task-1-report.md`. Tras las correcciones de misión y
  seguridad, el cierre literal fue `Spec Compliance: Approved`,
  `No remaining Critical or Important findings` y `Task quality: Approved`.
- Task 2 fue revisada por `/root/task2_review` usando
  `.superpowers/sdd/task-2-review.patch` y el reporte
  `.superpowers/sdd/task-2-report.md`. El cierre literal fue
  `Spec Compliance ✅`; Critical, Important y Minor: `None`; y
  `Task quality: Approved`.
- Task 3 fue revisada por `/root/task3_review` usando
  `.superpowers/sdd/task-3-review.patch` y el reporte
  `.superpowers/sdd/task-3-report.md`. El primer review detectó el gap
  Important de descubrimiento global sin curso; tras el fix TDD RED/GREEN, la
  re-review cerró con `Spec Compliance: Compliant`,
  `Remaining findings: None` y `Task quality: Approved`.
- Task 4 fue revisada por `/root/task4_review` usando
  `.superpowers/sdd/task-4-review.patch` y el reporte
  `.superpowers/sdd/task-4-report.md`. Cerró con
  `Spec Compliance: Compliant`, Critical/Important `None`, una nota Minor no
  bloqueante de hardening estructural del test estático en la línea 139, y
  `Task quality: Approved`.
- La evidencia consolidada se persistió en
  `artifacts/review-gates.txt`. No quedaron findings bloqueantes: el gate de
  Review estaba aprobado antes de iniciar Task 5 — validación independiente
  preliminar y antes de Documentación.

## Task 5 — validación independiente preliminar

- Static validation PASS; clean isolated Odoo run: 23 methods attempted, 22
  completed, one browser skip, 0 failures/errors (stats counter: 27).
- Browser behavior was not executed: websocket-client and Chrome/Chromium are
  absent from the image.
- Fresh HTTP fixtures passed course-less, independent-user, true two-course,
  legacy cross-course and batch-exclusion scenarios. Two earlier fixture
  attempts rolled back on required-field constraints before the supported
  direct-batch fixture passed.
- Fresh live asset resolution PASS: replacement 1, parent popup 0, share
  override 1, parent SCSS 1.
- Isolated database and ephemeral runtime removed; shared services remained Up
  and mounted the main checkout. No production code was edited by validator.
- `verification.json` is preliminary; complete revalidation is mandatory after
  documentation. No stage, commit, push or PR.

## Task 5 — Documentación

- Tras la validación preliminar satisfactoria, se documentó el addon sin editar
  Python, JavaScript, XML, CSV ni tests de runtime.
- Se creó `addons-extra/extrairg/irg_forum_notice_global_seen/README.md` con
  propósito, dependencia, instalación/actualización, semántica global
  `(usuario, publicación)`, compatibilidad legacy, autorización y visibilidad,
  comando de pruebas aislado mediante `docker-compose.local.yml` más overlay,
  y la limitación objetiva del navegador/persistencia.
- Se creó `missions/irg_forum_notice_global_seen/CHANGELOG.md`, registrando el
  addon nuevo, identidad global, endurecimiento de seguridad, corrección de la
  carrera de frontend, compatibilidad y la ausencia de migración o borrado de
  datos legacy.
- Se creó la entrada reutilizable
  `.agents/knowledge/odoo_development_modding/artifacts/forum_notice_global_seen.md`:
  identidad independiente del curso, servicios privados con `sudo()` técnico,
  rutas visibility-first, guardia CRUD legacy y replacement/polling seguro.
- Los checks documentales de placeholders Markdown, `git diff --check` y
  alcance Git se ejecutan y quedan reportados en
  `.superpowers/sdd/task-5-docs-report.md`. `verification.json` permanece sin
  cambios para la revalidación independiente final.

## Task 5 — revalidación independiente final

- Sobre el árbol final documentado, compileall, manifest/assets, ACL/rules,
  XML/CSV, JS, Markdown requerido, placeholders, knowledge, whitespace y alcance
  Git: PASS.
- Suite limpia final: 23 métodos intentados, 22 completados, un skip browser,
  0 fallos/errores; stats Odoo 27 tests. Browser no ejecutado porque faltan
  websocket-client y Chrome/Chromium.
- Escenarios HTTP finales course-less, usuarios independientes, multicurso
  real, legacy cross-course y exclusión por lote: PASS.
- Assets finales: replacement 1, parent popup 0, share override 1, SCSS parent
  1. PASS.
- Fixtures y base aislada eliminados; servidor/puerto efímeros ausentes; stack
  compartido Up y montando el checkout principal; addons existentes sin diff.
- `verification.json` sustituido por el gate final del árbol documentado con
  `status: passed`. Sin stage, commit, push ni PR.

## Task 5 — corrección de reproducibilidad de evidencia

- Se persistieron y ejecutaron validadores exactos bajo `artifacts/` para
  static/docs, fixtures, HTTP/assets, browser probe, cleanup y scope.
- Se repitió el comando Odoo literal: 23 intentados, 22 completados, un skip
  browser justificado, 0 fallos/errores; stats 27.
- `verification.json` contiene comandos literales y el gate Review aprobado.
- Cleanup/restauración repetidos; sin cambios de producción/docs ni acciones
  de publicación.

## Final-review fix wave — implementación/TDD

- El review final invalidó el gate anterior por interpolación HTML de payload
  no confiable, catch amplio de `IntegrityError`, cobertura course-less solo
  con system y ausencia de carrera concurrente determinista.
- RED XSS válido: `${` y campos del aviso aparecían en `innerHTML`; 1 fallo, 0
  errores. GREEN: skeleton estático, `textContent` y URL HTTP(S) same-origin.
- RED de integridad válido: una FK real terminó en `ForeignKeyViolation not
  raised`; 1 fallo, 0 errores. GREEN: `except UniqueViolation` recupera solo el
  duplicado y deja propagar el resto.
- Caracterización GREEN: `op.student` enlazado a usuario interno no-system, sin
  batch/curso/enrollment/admission, descubre, marca y suprime por rutas reales.
- Carrera GREEN: dos conexiones/transacciones sincronizadas ejecutan el método
  real; el ganador compromete, el perdedor dispara `UniqueViolation`, ambos
  recuperan el mismo id y queda una fila. Fixture comprometido limpiado.
- README separa `-i`/`-u`; changelog, knowledge y validadores cubren safe DOM,
  catch específico, porcelain exacto y servicios exactos.
- Estáticos PASS. Suite desde DB nueva: 28 intentados, 27 completados, un skip
  browser objetivo, stats 31, 0 fallos/errores. DBs y pycache eliminados;
  scope/restauración PASS.
- Por decisión explícita del usuario se acepta la prueba concurrente de dos
  transacciones DB reales; el experimento HTTP se retiró íntegramente y el
  último GREEN completo previo sigue siendo el árbol entregado.
- Sin stage, commit, push ni PR.
