# Ejecución — contrato estructural de política

## Task 1: RED

- Capacidad efectiva: `standard` (el runtime no permite seleccionar modelo explícitamente).
- Comando: `python3 missions/improve-agents-md/artifacts/validate_agents_policy.py`
- Exit code: `1` (fallo esperado antes de editar `AGENTS.md`).
- Contratos ausentes: `project_identity`, `lifecycle`, `coder_tdd`,
  `independent_validator`, `gate_rework`, `mission_levels`, `mission_artifacts`,
  `verification_json`, `check_results`, `knowledge_path`, `worktree_runtime`,
  `publication_separation`, `single_use_push` y `server_security`.
- Alcance: no se modificó `AGENTS.md`; este RED deja el contrato preparado para la
  posterior implementación de la política.

## Task 1: corrección tras revisión

- Causa raíz: los predicados anteriores buscaban términos en todo el documento y
  aceptaban coocurrencias sin relación normativa, negaciones y subcadenas.
- RED de regresión, antes de corregir el validador:
  `python3 -m unittest missions/improve-agents-md/artifacts/test_validate_agents_policy.py`
  terminó con exit `1`: 18 fallos esperados demostraron contradicciones aceptadas,
  placeholders no detectados, schema JSON insuficiente y falsos positivos `PR`/`UI`.
- GREEN: el mismo comando terminó con exit `0`: `Ran 22 tests`, `OK`.
- RED estructural vigente:
  `python3 missions/improve-agents-md/artifacts/validate_agents_policy.py` terminó
  con exit `1` y las 14 categorías ausentes originales. `AGENTS.md` no fue editado.
- Implementación: relaciones normativas acotadas por párrafo, tokens con límites,
  placeholders editoriales explícitos y validación tipada del ejemplo identificado
  como `verification.json`, incluida justificación no vacía para `skipped`.

## Task 1: segunda corrección tras revisión

- RED de regresión: la suite ampliada terminó con exit `1`, `Ran 30 tests`, con
  9 fallos y 2 errores `KeyError`. Reprodujo `[TODO]`/`[PENDIENTE]`, ausencia de
  claves JSON con claves extra y cláusulas válidas coexistiendo con excepciones
  contradictorias.
- Corrección: las claves obligatorias usan `required_keys.issubset(payload)` antes
  de acceder a ellas. Un catálogo de prohibiciones por contrato busca relaciones
  contradictorias completas dentro de cada párrafo, no términos globales sueltos.
- GREEN: `python3 -m unittest
  missions/improve-agents-md/artifacts/test_validate_agents_policy.py` terminó con
  exit `0`: `Ran 30 tests`, `OK`.
- El RED contra `AGENTS.md` vigente se volvió a ejecutar sin editarlo y mantuvo
  exit `1` con las 14 categorías de contrato ausentes.

## Task 1: tercera corrección tras revisión

- RED: la suite ampliada terminó con exit `1`, `Ran 37 tests`, con 7 fallos
  esperados. Cada fallo mantuvo una política conforme y añadió en otro párrafo una
  excepción contradictoria para identidad, lifecycle, niveles/artefactos de misión,
  verification JSON, resultados o ruta knowledge.
- Se extendió el catálogo local de prohibiciones a todas las categorías normativas.
  Incluye expresamente el caso `solo lectura -> misión full`, omitir gates del flujo,
  hacer obligatorio `diff.patch`, admitir YAML en `verification.json`, permitir skips
  sin justificación y aceptar rutas knowledge arbitrarias.
- GREEN: `python3 -m unittest
  missions/improve-agents-md/artifacts/test_validate_agents_policy.py` terminó con
  exit `0`: `Ran 37 tests`, `OK`.
- El RED vigente mantuvo exit `1` y 14 contratos ausentes sin editar `AGENTS.md`.

## Task 3: review y validación independiente

- Validador: agente distinto del codificador; no se editó `AGENTS.md`, el checker
  ni su suite de tests.
- Suite fresh: `python3 -m unittest
  missions/improve-agents-md/artifacts/test_validate_agents_policy.py` terminó con
  exit `0`: `Ran 37 tests`, `OK`.
- Checker fresh: `python3
  missions/improve-agents-md/artifacts/validate_agents_policy.py` terminó con exit
  `0`: `PASS: AGENTS.md satisfies all policy contracts`.
- El ejemplo `verification.json` de `AGENTS.md` se extrajo y parseó de forma
  independiente con `json.loads`; exit `0`, `PARSE PASS`.
- El scan independiente no encontró placeholders editoriales ni excepciones
  contradictorias conocidas. La revisión semántica confirmó propietarios, gates,
  capacidad soportada, proporcionalidad, runtime/worktrees, seguridad y publicación.
- `git diff --check` terminó con exit `0` y salida vacía. Las rutas `.txt`/`.json`
  de evidencia no están ignoradas por Git.
- Tras actualizar `origin/Dev_iRG`, la rama quedó `ahead 6, behind 1`; su diff
  triple-dot desde el merge-base contiene exclusivamente `AGENTS.md` y
  `missions/improve-agents-md/`. El commit remoto nuevo explica diferencias
  aparentes fuera de alcance en un diff directo y no pertenece a esta rama.
- No existe `codex/improve-agents-md` en el remoto. Ninguno de los seis commits
  únicos de la rama aparece en `refs/pull/*/head`; no hubo push ni PR de este
  trabajo. `gh pr list` no pudo resolver el repositorio privado con su identidad
  API, por lo que se usó la evidencia Git remota anterior.
- El checkout principal se inspeccionó en modo lectura y permanece en `Dev_iRG`;
  no se tocaron sus cambios locales ajenos.
- No se ejecutó runtime Odoo: el cambio es exclusivamente documental y de checker,
  sin módulos, configuración de runtime ni comportamiento Odoo modificado.
- Evidencia: `artifacts/validation-tests.txt`,
  `artifacts/validation-policy.txt` y `artifacts/validation-git-scope.txt`.

## Task 3: documentación

- La fase comenzó únicamente después de confirmar que
  `verification.json.status` era `passed` y que toda la evidencia referenciada
  estaba presente.
- Se creó `CHANGELOG.md` con el alcance funcional de la política, el checker, los
  gates de publicación y el resumen de validación independiente.
- Decisión de knowledge: no se creó una entrada separada. El aprendizaje
  reutilizable ya está expresado en el `AGENTS.md` canónico; duplicarlo en la
  knowledge base generaría dos fuentes susceptibles de divergir y contradiría la
  regla de evitar resúmenes duplicados.
- Concern de integración: la rama está un commit por detrás de
  `origin/Dev_iRG`. Antes de integrar se requiere rebase sobre la base remota
  actual y una nueva ejecución completa de los checks de validación.
- La entrega se limita a un commit local de los artefactos pendientes bajo
  `missions/improve-agents-md/`. No se modificó `AGENTS.md`, el checker, sus tests
  ni `verification.json` durante documentación; no se realizó push ni PR.

## Task 3: corrección de evidencia post-rebase

- Trazabilidad del plan: el plan detallado se escribió antes de comenzar Task 1.
  Permaneció sin commit durante Task 1 y Task 2 para aislar el staging de cada fase,
  y se versionó finalmente en Task 3 junto con la documentación de misión.
- Estado rebasado: base remota `e61a6742f`, política validada `956c046cc` y commit
  de documentación anterior a esta corrección `7792a74d3`.
- Se reemplazó la inferencia por igualdad de SHA con un checker versionable que
  hace fetch explícito de `refs/heads/*` y `refs/pull/*/head` a un namespace local,
  y comprueba por ancestry todos los commits de `origin/Dev_iRG..HEAD` contra cada
  ref obtenida.
- El checker ejecuta además exactamente `gh pr list --repo ivdevV/Odoo16iRG
  --state all --head codex/improve-agents-md --json number`. La consulta API no
  pudo resolver el repositorio; se conserva su salida y exit `1` como concern. El
  veredicto de publicación se limita al estado remoto Git observado actualmente y
  no afirma que históricamente nunca hubiera push o PR.
- Los checks redundantes de JSON embebido, placeholders y contradicciones se
  consolidaron en el checker real de política. Cada check restante de
  `verification.json` contiene el comando exacto reproducible que lo sustenta.

## Correcciones del review global: TDD y causa raíz

- Causa raíz del schema: `verification_example()` solo exigía `status` y `checks`;
  no comprobaba las claves completas ni la coherencia entre `status: passed` y un
  check `fail`.
- RED exacto: `python3 -m unittest
  missions/improve-agents-md/artifacts/test_validate_agents_policy.py` terminó con
  exit `1`, `Ran 41 tests`, 8 fallos esperados. Cubrió `passed` con `fail`, claves
  top-level ausentes, `command`/`evidence` ausentes y el gate de revalidación final.
- GREEN exacto: el mismo comando terminó con exit `0`, `Ran 41 tests`, `OK`.
- Implementación mínima: schema completo, coherencia `passed`/`fail`, salida exacta
  `AGENTS policy validation: PASS` y revalidación entre Documentación y Publicación.
- Causa raíz del inspector remoto: el checker hacía fetch a refs del repositorio
  compartido y actualizaba `refs/remotes/origin/Dev_iRG`.
- RED exacto: `python3 -m unittest
  missions/improve-agents-md/artifacts/test_check_remote_publication.py` terminó
  con exit `1` por ausencia de `PublicationCheckError` e
  `inspect_remote_publication`.
- GREEN exacto: el mismo comando terminó con exit `0`, `Ran 2 tests`, `OK`. Las
  pruebas usan repositorios Git locales, sin red, confirman que `origin/Dev_iRG` no
  cambia y que el snapshot se elimina tanto en éxito como en error.
- Corrección mínima: inspección dentro de un bare repo efímero gestionado por
  `TemporaryDirectory`; el checkout compartido solo se lee.
- Se eliminaron las líneas vacías finales de `plan.md` y `spec.md`; el gate final
  usa `git diff --check e61a6742f..HEAD`, no solo el working tree.

## Estrategia de revalidación final no circular

Los artefactos versionados registran los gates sobre el último commit funcional.
Después de crear el commit final de evidencia se vuelven a ejecutar, sin editar
ningún archivo, las dos suites, el checker, el parseo JSON, el diff completo, el
scope, el estado y el inspector remoto. Ese rerun post-commit es el veredicto sobre
el árbol realmente entregado y evita pretender que un archivo pueda certificar por
anticipado el commit que lo contiene.

## Corrección final del cleanup remoto

- RED: `python3 -m unittest
  missions/improve-agents-md/artifacts/test_check_remote_publication.py` terminó
  con exit `1`, `Ran 2 tests`, por `TypeError: unexpected keyword argument
  snapshot_origin_url`.
- La regresión hace que `ls-remote` use un origen local válido, permite crear el
  repositorio bare y solo entonces inyecta un origen inexistente para el fetch del
  snapshot. Así prueba un error dentro de `TemporaryDirectory`, no un fallo previo.
- GREEN: el mismo comando terminó con exit `0`, `Ran 2 tests`, `OK`.
- Se eliminaron 25 refs heredadas bajo el prefijo exacto
  `refs/validation/improve-agents-md/snapshot/*`. El comando incluyó un `case` que
  aborta ante cualquier nombre fuera del prefijo. Los listados posteriores del
  prefijo y del namespace de misión devolvieron salida vacía; no se tocaron otras
  refs.
- `validation-publication.txt` conserva el rerun post-commit de `eeea9ed58` y la
  observación posterior del commit funcional `4fb2ea17f`. Tras versionar esta
  evidencia se ejecuta otra vez el gate contra el nuevo HEAD y se entrega su SHA
  sin reabrir ni modificar los artefactos, manteniendo la validación no circular.
