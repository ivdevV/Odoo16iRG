# HomeClass Editions Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir varios HomeClass activos, priorizar la edición del lote y
probar las demás ediciones como respaldo sin mezclar notas.

**Architecture:** Crear un addon puente que hereda el mapa de curso, sus vistas
y el wizard. El modelo amplía el cálculo de `edition_year` para HomeClass con
periodos académicos y override manual; el wizard conserva el flujo existente
con cero o un candidato y usa una resolución ordenada por asignatura cuando hay
varios candidatos.

**Tech Stack:** Odoo 16 ORM, Python 3, XML views, `TransactionCase`,
`unittest.mock`.

## Global Constraints

- No modificar directamente `irg_gradebook_moodle_wizard`,
  `irg_gradebook_moodle_routing` ni
  `irg_gradebook_moodle_mapping_admin`.
- El addon nuevo vive bajo `addons-extra/extrairg/` y usa `_inherit`.
- Edición exacta primero; HomeClass genérico segundo; restantes por ID Moodle.
- El primer mapa que produzca una nota válida gana; nunca combinar notas.
- Un Activity ID inexistente permite probar el siguiente curso; una colisión
  real dentro del mismo curso permanece incompatible.
- Online mantiene su comportamiento actual.
- No borrar, desactivar ni reemplazar mapas o Activity IDs.
- No hay autorización de commit, push, PR ni despliegue.

---

### Task 1: Addon de ediciones HomeClass y fallback

**Files:**
- Create: `addons-extra/extrairg/irg_gradebook_moodle_homeclass_editions/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_homeclass_editions/__manifest__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_homeclass_editions/models/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_homeclass_editions/models/moodle_course_map.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_homeclass_editions/wizard/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_homeclass_editions/wizard/moodle_sync_wizard.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_homeclass_editions/views/moodle_course_map_views.xml`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_homeclass_editions/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_homeclass_editions/tests/test_homeclass_editions.py`

**Interfaces:**
- Produces:
  `extract_homeclass_start_year(name: str) -> int | False`.
- Extends:
  `irg.gradebook.moodle.course.map.edition_year` through
  `_compute_routing_metadata`.
- Adds:
  `irg_homeclass_edition_override: fields.Integer`.
- Adds wizard helpers:
  `_irg_homeclass_candidates()`,
  `_irg_order_homeclass_candidates(candidates)`,
  `_irg_load_multiple_homeclass(candidates)`.

- [ ] **Step 1: Write RED tests**

Cover period parsing for `-`, `/`, `_`; manual override; ordering exact,
generic, remaining; no exception with several HC; fallback when the first
course has no matching Activity ID; first valid course wins; Online delegates
unchanged.

- [ ] **Step 2: Run RED**

Run:

```bash
docker compose \
  -f /Users/ivrogo/Workspace/Proyectos\ iRG/Odoo16iRG/docker-compose.local.yml \
  -f .superpowers/sdd/docker-compose.worktree.yml run --rm --no-deps \
  odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -i irg_gradebook_moodle_homeclass_editions --test-enable \
  --test-tags /irg_gradebook_moodle_homeclass_editions \
  --stop-after-init --no-http --log-level=test
```

Expected: failures caused by the absent model/wizard behavior.

- [ ] **Step 3: Implement minimal addon**

Use a strict academic-period regexp:

```python
HOMECLASS_PERIOD_RE = re.compile(
    r"(?<!\d)(20\d{2})\s*[-/_]\s*(20\d{2})(?!\d)"
)
```

Accept only consecutive years. Extend the stored `edition_year` compute:
preserve `super()` for Online; for HomeClass assign override or parsed start
year.

For `action_load_moodle_data`, delegate to `super()` unless the batch is HC and
has more than one active candidate. With several candidates, order them and
evaluate each subject map in parent order. Reuse `_find_student_entry`,
`_grades_by_type` and `_compatibility_reason`. Persist only the first candidate
that yields at least one valid line for the subject. If none succeeds, create
one deterministic diagnostic line.

- [ ] **Step 4: Run GREEN and regression**

Run the addon suite, then:

```bash
docker compose \
  -f /Users/ivrogo/Workspace/Proyectos\ iRG/Odoo16iRG/docker-compose.local.yml \
  -f .superpowers/sdd/docker-compose.worktree.yml run --rm --no-deps \
  odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_gradebook_moodle_routing,irg_gradebook_moodle_mapping_admin,irg_gradebook_moodle_homeclass_editions \
  --test-enable \
  --test-tags /irg_gradebook_moodle_routing,/irg_gradebook_moodle_mapping_admin,/irg_gradebook_moodle_homeclass_editions \
  --stop-after-init --no-http --log-level=test
```

Expected: all tests pass with zero failures and zero errors.

- [ ] **Step 5: Static checks and Git scope**

Run `python3 -m compileall`, XML parsing, `git diff --check` and inspect
`git status --short`. Do not stage or commit.
