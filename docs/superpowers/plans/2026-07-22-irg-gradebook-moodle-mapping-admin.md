# iRG Gradebook Moodle Mapping Admin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Administrar e importar desde Odoo o `odoo shell` el mapeo curso Odoo → varios cursos Moodle → asignaturas Odoo → varios Activity IDs usando los dos CSV consolidados.

**Architecture:** Crear el addon puente `irg_gradebook_moodle_mapping_admin`, dependiente de `irg_gradebook_moodle_routing`, sin editar addons existentes. Un servicio común separará análisis sin escrituras y aplicación transaccional; el wizard binario y el wrapper de shell serán adaptadores de ese servicio. Los modelos actuales solo se extenderán con navegación y campos de presentación.

**Tech Stack:** Odoo 16, Python 3, ORM Odoo, `csv`, `dataclasses`, XML views, `TransactionCase`, `unittest.mock`, Docker Compose local.

## Global Constraints

- Especificación: `docs/superpowers/specs/2026-07-22-irg-gradebook-moodle-mapping-admin-design.md`.
- Todo el comportamiento nuevo vive en `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin`; no modificar addons existentes.
- Dependencia funcional: `irg_gradebook_moodle_routing`; versión inicial `16.0.1.0.0`.
- Entradas: `mapeo cursos.csv` y `Mapeo asignaturas.csv`, `;`, UTF-8 BOM o MacRoman.
- Máximo 10 MiB decodificados por fichero; antes de `b64decode` se limita el
  base64 a `4 * ceil(10 MiB / 3)` y `create`/`write` rechazan excesos; IDs entre
  1 y 2.147.483.647.
- El análisis no escribe mapas; la aplicación no llama a `commit`, `unlink`, ni reemplaza One2many completos.
- Filas sin Activity IDs se omiten; duplicados se deduplican preservando orden.
- Wizard limitado a `base.group_system` en ACL, UI y métodos server-side; no usar `sudo()`.
- Validación mediante `docker-compose.local.yml`, servicio `odoo_local`, base `test_irg_db`.
- Misión `full`, tier `complex`; Security Advisor previo y codificador, revisor y validador independientes.
- Commit, push, PR, despliegue e importación real requieren autorizaciones explícitas e independientes. Los checkpoints de commit no los autorizan.

---

## File Structure

```text
addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/
├── __init__.py
├── __manifest__.py
├── models/{__init__.py,moodle_mapping_admin.py}
├── services/{__init__.py,mapping_import.py}
├── wizard/{__init__.py,mapping_import_wizard.py}
├── tools/{__init__.py,import_mapping.py}
├── security/ir.model.access.csv
├── views/{moodle_mapping_admin_views.xml,mapping_import_wizard_views.xml}
├── tests/{__init__.py,common.py,test_mapping_admin_models.py,
│          test_mapping_import_analysis.py,test_mapping_import_apply.py,
│          test_mapping_import_wizard.py}
└── README.md

missions/irg-gradebook-moodle-mapping-admin/
├── plan.md
├── execution.md
├── verification.json
├── CHANGELOG.md
└── artifacts/{security-advisor.txt,red-tests.txt,green-tests.txt,
               review.txt,validation-tests.txt,real-csv-smoke.txt,scope-review.txt}
```

---

### Task 1: Mission and security gate

**Files:**
- Create: `missions/irg-gradebook-moodle-mapping-admin/plan.md`
- Create: `missions/irg-gradebook-moodle-mapping-admin/execution.md`
- Create: `missions/irg-gradebook-moodle-mapping-admin/artifacts/security-advisor.txt`

**Interfaces:**
- Consumes: approved design spec and repository `AGENTS.md`.
- Produces: mission scope and Security Advisor `[YES]` required before production code.

- [ ] **Step 1: Create mission artifacts before functional changes**

`plan.md` must copy the goal, file structure, fifteen acceptance cases from the spec, tier `complex`, Docker runtime and role ownership. Initialize `execution.md` exactly with:

```markdown
# Execution log — irg-gradebook-moodle-mapping-admin

- 2026-07-22: misión full/tier complex iniciada desde la especificación aprobada.
- Runtime: docker-compose.local.yml; DB: test_irg_db.
- Se preservan irg_gradebook_moodle_wizard e irg_gradebook_moodle_routing.
- Diseño/plan no autorizan commit, push, despliegue ni importación real.
```

- [ ] **Step 2: Obtain Security Advisor approval**

An independent advisor reviews: base64 and 10 MiB limits, CSV content handling, absence of web paths, `base.group_system`, direct RPC calls, no `sudo`, no commit/unlink, confirm-time revalidation and rollback. Store the full report; its last line must be `[YES] Reason: ...`. A `[NO]` amends the mission plan and blocks Task 2 until a new `[YES]`.

- [ ] **Step 3: Record baseline**

```bash
git status --short
git rev-parse HEAD
docker compose -f docker-compose.local.yml config --services
```

Expected: unrelated changes remain untouched; base commit recorded; `odoo_local` and `pgodoo_local` exist.

---

### Task 2: Scaffold and hierarchical presentation fields

**Files:**
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/__manifest__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/models/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/models/moodle_mapping_admin.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/wizard/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/security/ir.model.access.csv`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/views/moodle_mapping_admin_views.xml`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/views/mapping_import_wizard_views.xml`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/tests/common.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/tests/test_mapping_admin_models.py`

**Interfaces:**
- Consumes: existing course, subject and activity map models.
- Produces: inverse subject maps, numeric Odoo IDs, course context, subject code/name and activity summary.

- [ ] **Step 1: Write the failing model test**

The common fixture creates a course, linked subject, course map, subject map and activity IDs 395/397. Assert:

```python
def test_course_and_subject_context_fields(self):
    self.assertEqual(self.course_map.irg_op_course_database_id, self.course.id)
    self.assertEqual(self.course_map.irg_subject_map_ids, self.subject_map)
    self.assertEqual(self.course_map.irg_subject_map_count, 1)
    self.assertEqual(self.subject_map.irg_op_course_id, self.course)
    self.assertEqual(self.subject_map.irg_op_course_database_id, self.course.id)
    self.assertEqual(self.subject_map.irg_op_subject_database_id, self.subject.id)
    self.assertEqual(self.subject_map.irg_op_subject_name, self.subject.name)
    self.assertEqual(self.subject_map.irg_op_subject_code, self.subject.code)
    self.assertEqual(self.subject_map.irg_activity_count, 2)
    self.assertEqual(self.subject_map.irg_activity_ids_display, "395, 397")
```

- [ ] **Step 2: Run RED**

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -i irg_gradebook_moodle_mapping_admin --test-enable --test-tags /irg_gradebook_moodle_mapping_admin:TestMappingAdminModels --stop-after-init --log-level=test
```

Expected: FAIL because `irg_*` fields do not exist. Save the relevant output in `artifacts/red-tests.txt`.

- [ ] **Step 3: Implement the model extension**

Use these exact fields and computations:

```python
from odoo import api, fields, models


class IrgGradebookMoodleCourseMap(models.Model):
    _inherit = "irg.gradebook.moodle.course.map"

    irg_op_course_database_id = fields.Integer(
        string="ID curso Odoo", compute="_compute_irg_course_context"
    )
    irg_subject_map_ids = fields.One2many(
        "irg.gradebook.moodle.map", "course_map_id", string="Asignaturas Moodle"
    )
    irg_subject_map_count = fields.Integer(
        string="Asignaturas mapeadas", compute="_compute_irg_course_context"
    )

    @api.depends("op_course_id", "irg_subject_map_ids")
    def _compute_irg_course_context(self):
        for record in self:
            record.irg_op_course_database_id = record.op_course_id.id or 0
            record.irg_subject_map_count = len(record.irg_subject_map_ids)


class IrgGradebookMoodleMap(models.Model):
    _inherit = "irg.gradebook.moodle.map"

    irg_op_course_id = fields.Many2one(
        "op.course", related="course_map_id.op_course_id", readonly=True, store=True
    )
    irg_op_course_database_id = fields.Integer(
        string="ID curso Odoo", compute="_compute_irg_mapping_context"
    )
    irg_op_subject_database_id = fields.Integer(
        string="ID asignatura Odoo", compute="_compute_irg_mapping_context"
    )
    irg_op_subject_name = fields.Char(
        string="Nombre asignatura Odoo", related="op_subject_id.name", readonly=True
    )
    irg_op_subject_code = fields.Char(
        string="Código asignatura Odoo", related="op_subject_id.code", readonly=True
    )
    irg_activity_count = fields.Integer(
        string="Actividades", compute="_compute_irg_mapping_context"
    )
    irg_activity_ids_display = fields.Char(
        string="Activity IDs", compute="_compute_irg_mapping_context"
    )

    @api.depends("course_map_id.op_course_id", "op_subject_id", "line_ids.moodle_activity_id")
    def _compute_irg_mapping_context(self):
        for record in self:
            record.irg_op_course_database_id = record.course_map_id.op_course_id.id or 0
            record.irg_op_subject_database_id = record.op_subject_id.id or 0
            activity_ids = record.line_ids.sorted("moodle_activity_id").mapped(
                "moodle_activity_id"
            )
            record.irg_activity_count = len(activity_ids)
            record.irg_activity_ids_display = ", ".join(map(str, activity_ids))
```

Manifest: version `16.0.1.0.0`, depends `irg_gradebook_moodle_routing`, loads ACL then both view files. Root init imports `models` and `wizard`; the initial wizard init is empty. Create the ACL with its CSV header only and each initial XML file as a valid `<?xml version="1.0" encoding="utf-8"?><odoo/>`; Task 5 adds their functional records. This keeps the addon installable throughout TDD.

- [ ] **Step 4: Run GREEN**

Repeat Step 2. Expected: PASS and successful installation.

- [ ] **Step 5: Commit checkpoint**

Only with explicit authorization:

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_mapping_admin missions/irg-gradebook-moodle-mapping-admin
git commit -m "feat(gradebook): añadir contexto jerárquico al mapeo Moodle"
```

---

### Task 3: Read-only CSV analysis service

**Files:**
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/services/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/services/mapping_import.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/tests/test_mapping_import_analysis.py`

**Interfaces:**
- Produces: `ImportPlan` and `MappingImportService.analyze_bytes(bytes, bytes)`.
- Consumed by: apply, wizard and shell tasks.

- [ ] **Step 1: Write failing contract tests**

Production and tests use these immutable transport types:

```python
@dataclass(frozen=True)
class CourseOperation:
    op_course_id: int
    op_course_name: str
    moodle_course_id: int
    moodle_course_name: str


@dataclass(frozen=True)
class ActivityOperation:
    moodle_activity_id: int
    name: str


@dataclass(frozen=True)
class SubjectOperation:
    op_course_id: int
    op_course_name: str
    moodle_course_id: int
    op_subject_id: int
    op_subject_name: str
    op_subject_code: str
    moodle_course_name: str
    activities: tuple


@dataclass(frozen=True)
class ImportPlan:
    courses: tuple
    subjects: tuple
    summary: dict
```

Cover UTF-8 BOM/MacRoman, legacy/canonical headers, conflicting aliases, blank/no-activity rows, malformed/duplicate/out-of-range IDs, malformed Online markers, missing pair/record, membership, mismatched names/code, duplicate subject rows and name alignment.

- [ ] **Step 2: Run RED**

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_gradebook_moodle_mapping_admin --test-enable --test-tags /irg_gradebook_moodle_mapping_admin:TestMappingImportAnalysis --stop-after-init --log-level=test
```

Expected: FAIL importing `MappingImportService`.

- [ ] **Step 3: Implement bounded parsing and analysis**

Public skeleton and constants:

```python
CSV_DELIMITER = ";"
MAX_FILE_SIZE = 10 * 1024 * 1024
MIN_ID = 1
MAX_ID = 2147483647


class MappingImportService:
    def __init__(self, env):
        self.env = env

    def analyze_bytes(self, courses_payload, assignments_payload):
        course_rows = self._read_csv(courses_payload, "courses")
        assignment_rows = self._read_csv(assignments_payload, "assignments")
        courses, course_stats = self._analyze_courses(course_rows)
        subjects, subject_stats = self._analyze_subjects(assignment_rows, courses)
        return ImportPlan(
            tuple(courses.values()),
            tuple(subjects.values()),
            self._build_summary(course_stats, subject_stats),
        )


def _normalize_text(value):
    return " ".join(str(value or "").split()).casefold()
```

`_read_csv` rejects over 10 MiB, decodes UTF-8-SIG then MacRoman, uses `csv.DictReader(delimiter=";")`, tracks source lines from 2 and never evaluates cells. IDs require digits and global range. Courses resolve legacy/canonical aliases, reject conflicting values, validate `.browse(id).exists()`, normalized Odoo name and existing `parse_moodle_course_name`. Assignments require a pair from the same plan, Odoo existence/membership, normalized course/subject names and code, then merge by `(subject_id, moodle_course_id)`.

Fixed reason keys: `blank_row`, `invalid_id`, `invalid_online_marker`, `ambiguous_course_alias`, `missing_odoo_record`, `name_mismatch`, `code_mismatch`, `subject_not_in_course`, `missing_course_pair`, `conflicting_subject_parent`, `no_activity_ids`, `duplicate_activity_id`, `activity_name_count_mismatch`.

- [ ] **Step 4: Prove read-only GREEN**

Count the three persistent map models before/after `analyze_bytes` and assert equality. Repeat Step 2; all analysis tests must PASS.

- [ ] **Step 5: Commit checkpoint**

Only with explicit authorization:

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_mapping_admin missions/irg-gradebook-moodle-mapping-admin
git commit -m "feat(gradebook): analizar los dos CSV de mapeo Moodle"
```

---

### Task 4: Conservative transactional apply

**Files:**
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/services/mapping_import.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/tests/test_mapping_import_apply.py`

**Interfaces:**
- Consumes: `ImportPlan`.
- Produces: `MappingImportService.apply_plan(plan) -> dict`.

- [ ] **Step 1: Write failing upsert tests**

Test first creation, rerun idempotency, several Moodle courses per Odoo course, several activities per subject, preservation of existing `activity_type="assign"`, historical lines, non-empty name updates, parent integrity and this result shape:

```python
{
    "course_maps": {"created": 2, "updated": 0},
    "subject_maps": {"created": 2, "updated": 0},
    "activities": {"created": 4, "updated": 0},
    "affected_course_map_ids": [11, 12],
    "affected_subject_map_ids": [21, 22],
}
```

- [ ] **Step 2: Run RED**

Run the Task 3 command with tag `TestMappingImportApply`. Expected: FAIL because `apply_plan` is absent.

- [ ] **Step 3: Implement revalidated upsert**

```python
def apply_plan(self, plan):
    result = self._empty_apply_result()
    course_maps = {}
    for operation in plan.courses:
        self._revalidate_course(operation)
        record = self._upsert_course(operation, result)
        course_maps[(operation.op_course_id, operation.moodle_course_id)] = record
    for operation in plan.subjects:
        parent = course_maps[(operation.op_course_id, operation.moodle_course_id)]
        self._revalidate_subject(operation, parent)
        mapping = self._upsert_subject(operation, parent, result)
        self._upsert_activities(operation.activities, mapping, result)
    result["affected_course_map_ids"] = sorted(set(result["affected_course_map_ids"]))
    result["affected_subject_map_ids"] = sorted(set(result["affected_subject_map_ids"]))
    return result
```

Before any write, preflight the complete `ImportPlan`: tuple/member types,
unique course/subject/activity keys, non-empty subject activities and exact
parent identity. Invalid hand-built plans raise `ValidationError` without
dereferencing malformed entries or writing records. All searches use
`with_context(active_test=False)`. Upserts reactivate matches,
use existing SQL keys, preserve activity type, add without clearing, never
commit/unlink and repeat Odoo existence/name/code/membership/parent checks
immediately before writes. Names and code are compared against the source
values stored in `CourseOperation`/`SubjectOperation`; a concurrent change
raises `ValidationError` and aborts the transaction.

- [ ] **Step 4: Verify atomicity**

Patch `_upsert_activities` to raise `ValidationError` on the second subject inside a savepoint; assert the exception and zero records from that attempted application. Production must not catch an ORM failure and continue.

- [ ] **Step 5: Run GREEN and regression**

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_gradebook_moodle_routing,irg_gradebook_moodle_mapping_admin --test-enable --test-tags /irg_gradebook_moodle_routing,/irg_gradebook_moodle_mapping_admin --stop-after-init --log-level=test
```

Expected: new apply tests and all existing routing tests PASS.

- [ ] **Step 6: Commit checkpoint**

Only with explicit authorization:

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_mapping_admin missions/irg-gradebook-moodle-mapping-admin
git commit -m "feat(gradebook): aplicar el mapeo Moodle de forma idempotente"
```

---

### Task 5: Administrator wizard and inherited views

**Files:**
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/wizard/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/wizard/mapping_import_wizard.py`
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/security/ir.model.access.csv`
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/views/moodle_mapping_admin_views.xml`
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/views/mapping_import_wizard_views.xml`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/tests/test_mapping_import_wizard.py`

**Interfaces:**
- Consumes: analysis/apply service.
- Produces: `irg.gradebook.moodle.mapping.import.wizard` and four public actions.

- [ ] **Step 1: Write failing security/workflow tests**

An internal non-admin calling any action directly gets `AccessError`. Admin tests cover missing file, invalid base64, exactly 10 MiB, one decoded byte over, encoded payload over the derived maximum, direct RPC `create`/`write`, validate-without-writes, file-change reset, confirm-time reanalysis, applied state and filtered open actions. Patch `base64.b64decode` in the oversized-encoded test and assert it is not called.

- [ ] **Step 2: Run RED**

Run the Task 3 command with tag `TestMappingImportWizard`. Expected: transient model absent.

- [ ] **Step 3: Implement guarded wizard**

```python
class IrgGradebookMoodleMappingImportWizard(models.TransientModel):
    _name = "irg.gradebook.moodle.mapping.import.wizard"
    _description = "Importar mapeo Moodle"

    courses_file = fields.Binary(string="mapeo cursos.csv", required=True)
    courses_filename = fields.Char()
    assignments_file = fields.Binary(string="Mapeo asignaturas.csv", required=True)
    assignments_filename = fields.Char()
    state = fields.Selection(
        [("draft", "Borrador"), ("validated", "Validado"), ("applied", "Aplicado")],
        default="draft", required=True, readonly=True,
    )
    summary_text = fields.Text(readonly=True)
    affected_course_map_ids = fields.Many2many(
        "irg.gradebook.moodle.course.map", readonly=True
    )
    affected_subject_map_ids = fields.Many2many(
        "irg.gradebook.moodle.map", readonly=True
    )

    def _check_admin(self):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(_("Solo los administradores pueden importar el mapeo Moodle."))

    def _check_encoded_upload(self, value, label):
        if value is False or value is None:
            return
        if not isinstance(value, (bytes, str)):
            raise ValidationError(_("El archivo %s no es un binario válido.") % label)
        if len(value) > MAX_BASE64_SIZE:
            raise ValidationError(_("El archivo %s supera 10 MiB.") % label)

    def _decode_upload(self, value, label):
        if not value:
            raise ValidationError(_("Debe adjuntar %s.") % label)
        self._check_encoded_upload(value, label)
        try:
            payload = base64.b64decode(value, validate=True)
        except (ValueError, binascii.Error) as error:
            raise ValidationError(_("El archivo %s no es válido.") % label) from error
        if len(payload) > MAX_FILE_SIZE:
            raise ValidationError(_("El archivo %s supera 10 MiB.") % label)
        return payload
```

Define `MAX_BASE64_SIZE = 4 * ((MAX_FILE_SIZE + 2) // 3)`. Override
`@api.model_create_multi create` and `write` to call `_check_admin` and
`_check_encoded_upload` for each supplied binary before `super`; `write` also
resets state/summary/affected fields when a binary changes. Every public action
calls `_check_admin`, `ensure_one` and checks its allowed state; `action_apply`
requires `validated`. `action_validate` stores deterministic plain-text summary
only. `action_apply` decodes and analyzes again, applies, then uses `Command.set`
for affected maps. Never persist or trust a client-side plan.

- [ ] **Step 4: Add ACL and views**

ACL: one transient row for `base.group_system` with CRUD. Action/menu also use that group. Inherit routing course views to show Odoo ID, subject count and nested subject maps. Inherit routed subject views to show course/Moodle context, subject ID/name/code and activity count/list. Wizard uses statusbar and state-dependent Validate/Confirm/Open buttons.

- [ ] **Step 5: Run GREEN and XML check**

```bash
python3 - <<'PY'
from pathlib import Path
from lxml import etree
for path in Path('addons-extra/extrairg/irg_gradebook_moodle_mapping_admin').rglob('*.xml'):
    etree.parse(str(path))
print('XML OK')
PY
```

Repeat wizard test command. Expected: PASS, `XML OK`, addon upgrade without ACL/view errors.

- [ ] **Step 6: Commit checkpoint**

Only with explicit authorization:

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_mapping_admin missions/irg-gradebook-moodle-mapping-admin
git commit -m "feat(gradebook): añadir wizard administrativo de mapeo Moodle"
```

---

### Task 6: Shell adapter and operator documentation

**Files:**
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/tools/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/tools/import_mapping.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/README.md`
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/tests/test_mapping_import_analysis.py`

**Interfaces:**
- Produces: `analyze_paths(env, courses_path, assignments_path)` and `apply_plan(env, plan)`.

- [ ] **Step 1: Write failing adapter-equivalence test**

With `TemporaryDirectory`, write both payloads and assert `analyze_paths(...) == MappingImportService(env).analyze_bytes(...)`; over-10-MiB path fails before parsing.

- [ ] **Step 2: Run RED**

Run analysis tests. Expected: import of `tools.import_mapping` fails.

- [ ] **Step 3: Implement thin adapter**

```python
from pathlib import Path

from ..services.mapping_import import MAX_FILE_SIZE, MappingImportService


def _read_bounded(path):
    source = Path(path)
    if not source.is_absolute():
        raise ValueError("La ruta del CSV debe ser absoluta: %s" % source)
    with source.open("rb") as stream:
        payload = stream.read(MAX_FILE_SIZE + 1)
    if len(payload) > MAX_FILE_SIZE:
        raise ValueError("El CSV supera el límite de 10 MiB: %s" % source)
    return payload


def analyze_paths(env, courses_path, assignments_path):
    return MappingImportService(env).analyze_bytes(
        _read_bounded(courses_path), _read_bounded(assignments_path)
    )


def apply_plan(env, plan):
    return MappingImportService(env).apply_plan(plan)
```

- [ ] **Step 4: Write README**

Document hierarchy, table columns, wizard, reason keys, legacy headers, exact two-file shell snippet, explicit optional `env.cr.commit()`, read-only analysis, no deletion, 10 MiB, no-activity rule, missing `(8,24)`/`(8,47)` pairs, permissions, upgrade and rollback.

- [ ] **Step 5: GREEN and real-CSV read-only smoke**

Run full addon tests. In `odoo shell`, call only `analyze_paths` with `/Users/ivrogo/Downloads/mapeo cursos.csv` and `/Users/ivrogo/Downloads/Mapeo asignaturas.csv`. Record aggregate counts/reasons in `artifacts/real-csv-smoke.txt`; no row contents and no `apply_plan`. Expected: Online and HomeClass operations plus empty/no-activity/duplicate/missing-pair reasons, with zero writes.

- [ ] **Step 6: Commit checkpoint**

Only with explicit authorization:

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_mapping_admin missions/irg-gradebook-moodle-mapping-admin
git commit -m "docs(gradebook): documentar importación Moodle por UI y shell"
```

---

### Task 7: Independent review, validation and documentation closeout

**Files:**
- Create: `missions/irg-gradebook-moodle-mapping-admin/artifacts/review.txt`
- Create: `missions/irg-gradebook-moodle-mapping-admin/artifacts/validation-tests.txt`
- Create: `missions/irg-gradebook-moodle-mapping-admin/artifacts/scope-review.txt`
- Create: `missions/irg-gradebook-moodle-mapping-admin/verification.json`
- Create: `missions/irg-gradebook-moodle-mapping-admin/CHANGELOG.md`
- Modify: `missions/irg-gradebook-moodle-mapping-admin/execution.md`
- Modify: `.agents/knowledge/odoo_development_modding/artifacts/irg_gradebook_moodle_course_activity_routing.md`

**Interfaces:**
- Consumes: final functional diff.
- Produces: independent approvals and `verification.json` with `status: passed`.

- [ ] **Step 1: Independent code review**

Reviewer checks requirements, tests, ACL/runtime XML, new-addon-only scope, no `sudo`/commit/unlink, bounded reads, server guard, parent integrity, no cell evaluation, stable dedupe, idempotency and historical preservation. Store approval in `review.txt`. Blocking findings return to implementation and require fresh review.

- [ ] **Step 2: Independent validation**

```bash
python3 -m compileall -q addons-extra/extrairg/irg_gradebook_moodle_mapping_admin
python3 -c "import ast, pathlib; ast.literal_eval(pathlib.Path('addons-extra/extrairg/irg_gradebook_moodle_mapping_admin/__manifest__.py').read_text())"
docker compose -f docker-compose.local.yml exec -T odoo_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_gradebook_moodle_routing,irg_gradebook_moodle_mapping_admin --test-enable --test-tags /irg_gradebook_moodle_routing,/irg_gradebook_moodle_mapping_admin --stop-after-init --log-level=test
git diff --check
```

Validator saves concise evidence. Any failure sets verification to failed and reopens implementation.

- [ ] **Step 3: UI smoke and cleanup**

Admin verifies both tables/columns and validates both uploaded CSV copies, then cancels without applying. Internal user has no menu and RPC denial is covered. Remove transient fixtures and restore the shared runtime to the original checkout; record evidence without credentials/data rows.

- [ ] **Step 4: Emit verification and reusable docs**

`verification.json` follows repository schema, contains commands/results/evidence, Docker/DB/base commit, tier `complex`, escalations and `status: passed`. CHANGELOG records UI/shell parity, two-file import, omissions/dedupe and conservative upsert. Knowledge receives only reusable patterns: shared service, legacy aliases, confirm-time reanalysis and read-only preview.

- [ ] **Step 5: Bounded final consistency check**

```bash
git status --short
git diff --check
python3 -m json.tool missions/irg-gradebook-moodle-mapping-admin/verification.json >/dev/null
```

Expected: intended addon/spec/plan/mission/knowledge files plus untouched pre-existing user changes; verification parses and is passed.

- [ ] **Step 6: Authorized publication handoff**

Ask separately for commit, push to SSH `origin/Dev_iRG`, Dev addon upgrade and real data import. Only after explicit commit authorization:

```bash
git add addons-extra/extrairg/irg_gradebook_moodle_mapping_admin docs/superpowers/specs/2026-07-22-irg-gradebook-moodle-mapping-admin-design.md docs/superpowers/plans/2026-07-22-irg-gradebook-moodle-mapping-admin.md missions/irg-gradebook-moodle-mapping-admin .agents/knowledge/odoo_development_modding/artifacts/irg_gradebook_moodle_course_activity_routing.md
git commit -m "feat(gradebook): administrar e importar el mapeo Moodle jerárquico"
```

Do not push until a new one-use authorization explicitly names SSH remote `origin`, branch `Dev_iRG` and this commit scope.
