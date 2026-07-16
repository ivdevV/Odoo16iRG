# AGENTS.md Workflow Policy Improvement Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to execute this plan. Steps use checkbox syntax for tracking.

**Goal:** Reescribir `AGENTS.md` como una política ejecutable, proporcional y coherente para el desarrollo de Odoo16iRG.

**Architecture:** Mantener un único documento raíz como fuente canónica. Una prueba estructural de política define los contratos mínimos; la reescritura debe satisfacerla y después superar review y validación independientes.

**Tech Stack:** Markdown, Python 3 estándar, Git y Docker Compose local como contrato documental.

## Global Constraints

- Modificar únicamente `AGENTS.md` y los artefactos de `missions/improve-agents-md/`.
- No modificar módulos Odoo ni configuración de runtime.
- Preservar la prohibición de push a `Dev_iRG` sin autorización explícita nueva.
- Usar capacidad `standard`; los artefactos de misión no cuentan para el tier funcional.
- No hacer commit final, push ni PR sin completar review y `verification.json` `passed`.

---

### Task 1: Crear el contrato estructural en RED

**Files:**
- Create: `missions/improve-agents-md/artifacts/validate_agents_policy.py`
- Create: `missions/improve-agents-md/execution.md`
- Test: `AGENTS.md`

**Interfaces:**
- Consumes: `missions/improve-agents-md/spec.md` y el `AGENTS.md` vigente.
- Produces: un comando determinista que sale `0` solo cuando la política cumple los criterios aprobados.

- [ ] **Step 1: Crear el validador de política**

El script debe leer `AGENTS.md` desde la raíz y comprobar:

- nombre real `Odoo16iRG`, sin placeholders editoriales;
- flujo exacto Plan, Implementación/TDD, Review, Validación, Documentación y Publicación;
- TDD propiedad del codificador con RED y GREEN;
- validador independiente sin edición de producción;
- gates fallidos que reabren implementación y escalado separado de corrección;
- misiones `none`, `light` y `full` proporcionales;
- `execution.md`, evidencia concisa y `diff.patch` opcional;
- bloque `verification.json` extraíble y parseable con `json.loads`;
- resultados `pass`, `fail`, `skipped` y justificación de skips;
- ruta canónica `.agents/knowledge/odoo_development_modding/artifacts/`;
- `docker-compose.local.yml`, overlay de worktree, cleanup y restauración;
- separación explícita de commit, push y PR;
- autorización de push de un solo uso para remoto, rama y alcance concretos;
- controles de servidor para acciones protegidas, no solo restricciones UI.

- [ ] **Step 2: Ejecutar RED antes de editar AGENTS.md**

Run: `python3 missions/improve-agents-md/artifacts/validate_agents_policy.py`

Expected: exit distinto de cero con una lista de contratos ausentes en el documento vigente.

- [ ] **Step 3: Registrar RED**

Añadir a `execution.md` el comando, exit code y categorías ausentes. No copiar salida repetitiva.

### Task 2: Reescribir AGENTS.md

**Files:**
- Modify: `AGENTS.md`
- Test: `missions/improve-agents-md/artifacts/validate_agents_policy.py`

**Interfaces:**
- Consumes: contrato RED de Task 1 y `spec.md` aprobado.
- Produces: política raíz canónica para todos los agentes del proyecto.

- [ ] **Step 1: Sustituir placeholders y definir alcance**

Definir explícitamente qué tareas no requieren misión, cuáles usan misión ligera y cuáles misión completa. La clasificación funcional no incluirá los archivos de la propia misión.

- [ ] **Step 2: Definir lifecycle y propietarios**

Documentar `Plan → Implementación/TDD → Review → Validación → Documentación → Publicación autorizada`, con independencia de roles y condiciones de avance.

- [ ] **Step 3: Definir routing, gates y bucles correctivos**

Mantener `trivial → standard → complex`, describir capacidad requerida cuando no se pueda seleccionar modelo y hacer que cualquier gate fallido reabra implementación. En `complex`, corregir y revalidar sin inventar otro escalado.

- [ ] **Step 4: Definir artefactos y verificación válida**

Usar `execution.md`, evidencia concisa compatible con `.gitignore`, `diff.patch` opcional y un ejemplo JSON sin comentarios que incluya checks, comandos, evidencia, entorno, tier y escalados.

- [ ] **Step 5: Definir Odoo local, aislamiento y cleanup**

Exigir `docker-compose.local.yml`; si el compose monta el checkout principal, usar overlay para el worktree. Restaurar servicio y limpiar fixtures temporales con evidencia.

- [ ] **Step 6: Definir seguridad, knowledge y publicación**

Cerrar los disparadores Security Advisor, el ciclo `[NO] → enmienda → [YES]`, controles server-side, ubicación real de knowledge y autorización granular de commit/push/PR.

- [ ] **Step 7: Ejecutar GREEN**

Run: `python3 missions/improve-agents-md/artifacts/validate_agents_policy.py`

Expected: `AGENTS policy validation: PASS` y exit `0`.

### Task 3: Review y validación independiente

**Files:**
- Modify: `missions/improve-agents-md/execution.md`
- Create: `missions/improve-agents-md/verification.json`
- Create: `missions/improve-agents-md/CHANGELOG.md`

**Interfaces:**
- Consumes: `AGENTS.md`, `spec.md`, validador y evidencia RED/GREEN.
- Produces: veredicto independiente y documentación final de la misión.

- [ ] **Step 1: Review independiente**

Comprobar contradicciones, placeholders, autoridad, loops imposibles, selección de capacidades no soportada, compatibilidad con `.gitignore`, proporcionalidad y preservación de la regla de no-push.

- [ ] **Step 2: Validación independiente**

Run:

```bash
python3 missions/improve-agents-md/artifacts/validate_agents_policy.py
python3 -m json.tool missions/improve-agents-md/verification.json
git diff --check
```

Expected: todos exit `0`; `verification.json.status` será `passed` únicamente si todos los checks relevantes pasan.

- [ ] **Step 3: Documentación**

Crear changelog conciso. Solo crear una entrada de knowledge si existe un aprendizaje reutilizable que no quede ya expresado en `AGENTS.md`.

- [ ] **Step 4: Gate final local**

Verificar que el diff contiene únicamente `AGENTS.md` y `missions/improve-agents-md/`, que no existe push/PR y que el checkout principal continúa intacto.
