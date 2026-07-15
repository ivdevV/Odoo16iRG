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
