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
