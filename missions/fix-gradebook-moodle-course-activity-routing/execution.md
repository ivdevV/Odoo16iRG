# Ejecución

- 2026-07-22: misión creada desde `Dev_iRG` en el worktree aislado
  `codex/gradebook-moodle-routing`.
- 2026-07-22: consultadas las reglas Odoo, el plan previo, el addon desplegado
  y los patrones de addons puente del proyecto.
- 2026-07-22: confirmado que `app.gradebook.student` expone `course_id` y
  `batch_id`, y que los códigos de lote se generan con los tokens `HC`/`ONL`.
- 2026-07-22: diseño corregido según los tres CSV y la aclaración del usuario.
- 2026-07-22: baseline Docker del addon heredado: 44 métodos / 50 tests y
  subtests, 0 fallos, 0 errores. Evidencia `artifacts/baseline.txt`.
- 2026-07-22: inspeccionados únicamente los encabezados y encoding de los
  tres CSV reales; confirmado MacRoman, separador `;`. No se ejecutó ninguna
  importación real.
- 2026-07-22: creados tests y placeholders mínimos del addon nuevo antes de
  lógica funcional. Un primer intento no descubrió tests porque el
  `tests/__init__.py` quedó fuera del addon; se corrigió el archivo de
  descubrimiento y se repitió RED, sin considerar válido el intento de cero
  tests.
- 2026-07-22: RED válido con upgrade Docker: exit 1, 10 métodos / 12
  tests-subtests, 11 fallos y 1 error por comportamientos ausentes. Evidencia
  `artifacts/red.txt`.
- 2026-07-22: implementados modelo y metadatos de curso, relación padre,
  filtro contextual, selección HC/ONL, importador MacRoman idempotente, ACL y
  vistas, exclusivamente en `irg_gradebook_moodle_routing`.
- 2026-07-22: primer GREEN funcional: 10 métodos / 12 tests-subtests, 0
  fallos y 0 errores.
- 2026-07-22: autocritica detectó que el override resolvía routing antes del
  guard de acceso. Se añadió una regresión enfocada y se observó RED con
  `UserError` en lugar del `AccessError` canónico; se movió el guard antes del
  routing y se mantuvo también el guard heredado posterior.
- 2026-07-22: GREEN final Docker: exit 0, 11 métodos / 13 tests-subtests, 0
  fallos y 0 errores. Evidencia `artifacts/green.txt`.
- 2026-07-22: `compileall`, AST del manifest, parse XML, parse ACL,
  `git diff --check` y scan de whitespace superados. El contenedor efímero se
  eliminó y el servicio compartido continuó montando el checkout principal.
- 2026-07-22: estado Git comprobado. No se hizo stage, commit, push ni PR.
- 2026-07-22: Review independiente devolvió la misión a Implementación por
  tres findings bloqueantes: coherencia padre/hijo, reset destructivo de
  líneas y diagnóstico incompleto de autorizadores/headers.
- 2026-07-22: añadidas primero regresiones para los tres findings y fixtures
  con nombres incompletos, autorizadores inválidos y headers ausentes. Tras
  corregir un defecto del propio writer del fixture, RED válido: exit 1, 16
  métodos / 18 tests-subtests, 7 fallos y 1 error. Evidencia
  `artifacts/review-fix-red.txt`.
- 2026-07-22: añadida constraint ORM en mapas de asignatura para igualdad de
  Moodle Course ID y pertenencia al curso Odoo padre, constraint recíproca
  para impedir que una edición del padre corrompa hijos existentes, y defensa
  del wizard sobre históricos antes de `_get_service`.
- 2026-07-22: reemplazado el reset `(5, 0, 0)` por upsert de líneas por
  Activity ID. Las líneas ausentes del CSV se preservan, los IDs permanecen
  estables y los metadatos existentes solo se actualizan cuando la fuente
  aporta nombre; el tipo existente no se fuerza.
- 2026-07-22: el importador valida headers obligatorios y devuelve por fuente
  filas leídas, aceptadas, descartadas y motivos agregados, incluidas las
  incidencias estructurales HomeClass/online.
- 2026-07-22: un microciclo RED adicional demostró que editar el padre podía
  invalidar hijos; se amplió la constraint al modelo de curso y quedó GREEN.
- 2026-07-22: GREEN final de Review fix: exit 0, 17 métodos / 19
  tests-subtests, 0 fallos y 0 errores. Evidencia
  `artifacts/review-fix-green.txt`.
- 2026-07-22: repetidos compileall, AST manifest, XML, ACL, diff, whitespace,
  ausencia de reset destructivo, overlay y restauración; todos pasaron. Git
  permanece sin stage, commit, push ni PR.
- 2026-07-22: Validación independiente: upgrade y suite del addon en
  `test_irg_db` con el overlay del worktree superados (17 métodos / 19 tests y
  subtests, 0 fallos, 0 errores). Se ejecutó el importador contra los tres CSV
  reales dentro de Odoo con `SAVEPOINT`, rollback y liberación explícita; la
  base de test no contiene los registros Odoo fuente, así que las 410 filas de
  asignaturas se descartaron sin persistencia y se confirmó que Odoo 1/Moodle
  36 sigue sin mapa. El parseo, autorizaciones y rollback pasaron.
- 2026-07-22: La validación estática detectó un fallo bloqueante de
  `git diff --check --no-index` sobre archivos funcionales no versionados:
  `__init__.py`, `models/__init__.py`, `tests/__init__.py` y
  `wizard/__init__.py` tienen una línea en blanco extra al EOF. Por contrato,
  `verification.json` queda en `failed` hasta que Implementación corrija ese
  whitespace y se repita Validación. La comprobación de restauración confirmó
  que no quedaron contenedores efímeros y el servicio compartido continúa
  montando el checkout principal.
- 2026-07-22: TDD no aplica objetivamente al fix porque elimina únicamente la
  línea vacía adicional al EOF de los `__init__.py` del addon raíz, `models`,
  `tests` y `wizard`, sin cambiar imports, lógica ni comportamiento. Se aplicó
  la corrección y pasaron `git diff --check --no-index`, `compileall`, parse AST
  de imports y la aserción de un único newline final.
- 2026-07-22: Re-review acotada confirmó que los cuatro `__init__.py` mantienen
  exactamente los mismos imports y un único newline POSIX; conservó
  `Spec compliance: PASS`, `Code quality: APPROVED` y
  `Readiness: READY_FOR_INDEPENDENT_VALIDATION`.
- 2026-07-22: Tras el fix de whitespace y su Re-review se repitió la
  Validación independiente completa sin reutilizar resultados: los 12 archivos
  funcionales pasaron `compileall`, manifest AST, XML, ACL, alcance,
  `git diff --check`, diff `--no-index` y scan no destructivo. Upgrade y suite
  Odoo pasaron de nuevo en `test_irg_db` (17 métodos / 19 tests y subtests, 0
  fallos, 0 errores). El importador se volvió a ejecutar con los tres CSV
  reales mediante savepoint y rollback explícito; confirmó el mismo resumen
  agregado, ausencia de Odoo 1/Moodle 36 y restauración exacta de conteos. No
  quedaron contenedores efímeros, el servicio compartido sigue montando el
  checkout principal y Git permanece sin stage, commit, push ni PR.
  `verification.json` queda en `passed`.
- 2026-07-22: Documentación posterior a Review y Validación: creado el README
  operativo del addon, actualizado el changelog y registrada la decisión de
  conocimiento reutilizable. No se modificaron código, pruebas, seguridad,
  datos ni configuración funcional. Autocheck superado: enlace relativo a
  `verification.json` resuelto, Markdown UTF-8 con newline final y sin tabs,
  coherencia con la validación aprobada y `git diff --check`/`--no-index` de
  los cuatro archivos documentales sin whitespace errors. No se hizo stage,
  commit, push ni PR.
- 2026-07-22: Review final reabrió Implementación por el fallback inseguro de
  marcadores Online malformados y pidió aislar una regresión de mutaciones del
  padre. Se separaron los dos casos parentales con fixtures independientes y
  se añadieron primero regresiones para `(ONLINE2026)`, `(online 26)` y
  `(OnLiNe 2026 EXTRA)` en cómputo, importador y wizard pre-Moodle.
- 2026-07-22: RED válido del fix final: exit 1, 20 métodos / 22 tests-subtests,
  5 fallos esperados y 0 errores. Evidencia
  `artifacts/final-review-fix-red.txt`.
- 2026-07-22: implementado un parser determinista compartido: sin marcador es
  HomeClass; solo `(ONLINE)` es genérico y `(ONLINE AAAA)` edición; cualquier
  nombre que contenga `(ONLINE` sin coincidir exactamente queda sin modalidad.
  El importador registra `invalid_online_marker` y el wizard no puede escoger
  esos mapas, por lo que bloquea antes de `_get_service`.
- 2026-07-22: GREEN completo: exit 0, 20 métodos / 22 tests-subtests, 0 fallos
  y 0 errores. Compileall, manifest AST, XML, ACL, whitespace, diff de
  untracked, scan anti-reset, overlay/restauración y estado Git pasaron.
  Evidencia `artifacts/final-review-fix-green.txt`. No se modificaron
  CHANGELOG, README ni knowledge en esta reapertura y no se hizo stage,
  commit, push ni PR.
- 2026-07-22: Re-review funcional independiente cerró el finding Important del
  marcador Online malformado y el Minor del test parental. Aprobó el parser
  compartido, el descarte `invalid_online_marker` y el bloqueo pre-Moodle, sin
  findings abiertos, para una nueva Validación independiente.
- 2026-07-22: Validación independiente de la versión final funcional repetida
  desde cero. Los estáticos pasaron sobre los 12 archivos funcionales y el
  README; la suite Odoo también pasó (20 métodos / 22 tests-subtests, 0 fallos,
  0 errores). El import de los tres CSV reales pasó con savepoint/rollback,
  conteos restaurados y Odoo 1/Moodle 36 excluido. Un smoke sintético adicional
  confirmó que tres markers Online malformados se contabilizan como
  `invalid_online_marker`, no crean/actualizan mapas y dejan conteos idénticos.
- 2026-07-22: El upgrade emitió un `ERROR/3` y varios `WARNING/2` de docutils
  al procesar `README.md` del propio addon (bloques Markdown incompatibles con
  el parser reStructuredText usado por Odoo). El README además conserva la
  descripción anterior de que todo nombre con `(ONLINE` es Online, en
  contradicción con el parser final que rechaza markers malformados. Aunque el
  proceso devolvió exit 0 y todos los tests pasaron, el gate de upgrade limpio
  falla y `verification.json` queda en `failed`. El defecto es documental; no
  se editó producción ni tests. Cleanup/restauración y Git pasaron, sin stage,
  commit, push ni PR.
- 2026-07-22: Documentación corrigió el README a reStructuredText compatible
  con docutils, alineó la regla exacta `(ONLINE)` / `(ONLINE AAAA)`, completó
  el changelog funcional, actualizó knowledge y ordenó cronológicamente este
  registro. Docutils 0.16 del contenedor Odoo procesó el README con
  `halt_level=2` sin warnings ni errores; también pasaron la coherencia
  documental y `git diff --check`/`--no-index`. No se modificaron código,
  tests, seguridad, datos ni configuración funcional; la revalidación del
  upgrade queda pendiente. No se hizo stage, commit, push ni PR.
- 2026-07-22: Revalidación independiente completa tras la corrección
  documental: el upgrade y la suite pasaron (20 métodos / 22 tests-subtests,
  0 fallos, 0 errores, exit 0) y la captura completa no contiene `docutils`,
  `ERROR/3` ni `WARNING/2` atribuibles al README. Pasaron también compileall,
  manifest AST, XML, ACL, contrato documental, alcance, diff tracked y de los
  13 archivos untracked del addon, y scan anti-reset. El import real de los
  tres CSV repitió el resumen esperado con rollback y Odoo 1/Moodle 36
  excluido; el smoke sintético repitió 3 descartes
  `invalid_online_marker`, 0 mapas y rollback. Cleanup/restauración y Git
  pasaron. `verification.json` queda en `passed`; no se editó producción,
  tests ni documentación y no se hizo stage, commit, push ni PR.
