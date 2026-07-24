# Moodle `iteminstance` Matching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolver los IDs de actividad importados desde los CSV contra `id`,
`cmid` o `iteminstance` de Moodle, incluyendo el fallback entre ediciones
HomeClass.

**Architecture:** Crear un addon puente nuevo que dependa del sincronizador y
del addon de ediciones HomeClass. El addon sobrescribirá únicamente el servicio
creado por el wizard y los dos puntos de resolución de IDs, preservando los
addons existentes y sus contratos.

**Tech Stack:** Odoo 16, Python 3, `TransactionCase`, herencia de modelos Odoo,
servicios REST Moodle existentes.

## Global Constraints

- No modificar addons existentes; implementar mediante un addon puente nuevo.
- Aceptar `id`, `cmid` e `iteminstance` sin cambiar ni reimportar los CSV.
- Una coincidencia del mismo item por varios campos cuenta una sola vez.
- Cero candidatos significa no encontrado; más de uno significa ambiguo.
- Mantener validación de `itemmodule`, reutilización, notas y escala.
- El fallback HomeClass solo continúa ante ausencia recuperable.
- Usar `docker-compose.local.yml` para toda validación Odoo.
- No hacer commit, push ni despliegue sin autorización explícita separada.

---

### Task 1: Crear la misión y el addon puente con una prueba RED

**Files:**
- Create: `missions/fix-gradebook-moodle-iteminstance-matching/plan.md`
- Create: `missions/fix-gradebook-moodle-iteminstance-matching/execution.md`
- Create: `missions/fix-gradebook-moodle-iteminstance-matching/docker-compose.worktree.yml`
- Create: `missions/fix-gradebook-moodle-iteminstance-matching/artifacts/`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/__manifest__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/models/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/models/gradebook_service.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/wizard/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/wizard/moodle_sync_wizard.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/tests/__init__.py`
- Create: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/tests/test_iteminstance_matching.py`

**Interfaces:**
- Consumes: `GradebookMoodleService`, modelo
  `irg.gradebook.moodle.sync.wizard` y
  `IrgGradebookMoodleSyncWizard._irg_resolution_conflict`.
- Produces: addon instalable `irg_gradebook_moodle_iteminstance`.

- [ ] **Step 1: Crear el manifiesto mínimo**

```python
{
    "name": "iRG Gradebook Moodle Iteminstance",
    "version": "16.0.1.0.0",
    "category": "Website/eLearning",
    "summary": "Resuelve actividades Moodle por id, cmid o iteminstance",
    "author": "iRG",
    "depends": ["irg_gradebook_moodle_homeclass_editions"],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
```

- [ ] **Step 2: Escribir pruebas que describan la resolución requerida**

Crear casos para:

```python
def test_matches_activity_by_iteminstance(self):
    result = self.wizard._irg_match_grade_items(
        [{"id": 555, "cmid": 3290, "iteminstance": 205}], 205
    )
    self.assertEqual([(0, result[0][1])], result)

def test_same_item_matching_two_fields_is_not_ambiguous(self):
    result = self.wizard._irg_match_grade_items(
        [{"id": 205, "cmid": 3290, "iteminstance": 205}], 205
    )
    self.assertEqual(1, len(result))

def test_different_items_across_namespaces_are_ambiguous(self):
    result = self.wizard._irg_match_grade_items(
        [
            {"id": 205, "cmid": 3290, "iteminstance": 999},
            {"id": 777, "cmid": 888, "iteminstance": 205},
        ],
        205,
    )
    self.assertEqual(2, len(result))
```

- [ ] **Step 3: Ejecutar RED**

Run:

```bash
docker compose -f docker-compose.local.yml \
  -f missions/fix-gradebook-moodle-iteminstance-matching/docker-compose.worktree.yml \
  run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d irg_iteminstance_test \
  -i irg_gradebook_moodle_iteminstance --test-enable \
  --test-tags=/irg_gradebook_moodle_iteminstance --stop-after-init
```

Expected: fallo porque `_irg_match_grade_items` todavía no existe.

- [ ] **Step 4: Guardar la salida RED**

Guardar el resultado conciso en
`missions/fix-gradebook-moodle-iteminstance-matching/artifacts/red-tests.txt`
y registrar comando y resultado en `execution.md`.

### Task 2: Validar `iteminstance` y usar el servicio especializado

**Files:**
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/models/gradebook_service.py`
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/wizard/moodle_sync_wizard.py`
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/tests/test_iteminstance_matching.py`

**Interfaces:**
- Produces:
  `IteminstanceGradebookMoodleService._validate_grade_payload(payload) -> list`
  y `IrgGradebookMoodleSyncWizard._get_service() -> IteminstanceGradebookMoodleService`.

- [ ] **Step 1: Añadir pruebas RED del esquema**

```python
def test_service_accepts_integer_iteminstance(self):
    payload = self._payload(iteminstance=205)
    self.assertEqual(
        payload["usergrades"],
        IteminstanceGradebookMoodleService._validate_grade_payload(payload),
    )

def test_service_rejects_non_integer_iteminstance(self):
    with self.assertRaisesRegex(UserError, "respuesta recibida"):
        IteminstanceGradebookMoodleService._validate_grade_payload(
            self._payload(iteminstance="205")
        )
```

Incluir además `None` y `0` como valores válidos.

- [ ] **Step 2: Ejecutar RED del servicio**

Run: el comando Odoo de Task 1 con
`--test-tags=/irg_gradebook_moodle_iteminstance:TestIteminstanceService`.

Expected: fallo por ausencia de la clase o de la validación.

- [ ] **Step 3: Implementar el servicio mínimo**

```python
class IteminstanceGradebookMoodleService(GradebookMoodleService):
    @classmethod
    def _validate_grade_payload(cls, payload):
        usergrades = super()._validate_grade_payload(payload)
        for usergrade in usergrades:
            for item in usergrade["gradeitems"]:
                value = item.get("iteminstance")
                if value is not None and type(value) is not int:
                    cls._raise_invalid_response()
        return usergrades
```

Sobrescribir `_get_service` en el wizard usando las mismas credenciales y el
mismo mensaje seguro del addon base.

- [ ] **Step 4: Ejecutar GREEN del servicio**

Run: el mismo comando del Step 2.

Expected: todas las pruebas del servicio pasan.

### Task 3: Resolver IDs mediante `id`, `cmid` o `iteminstance`

**Files:**
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/wizard/moodle_sync_wizard.py`
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/tests/test_iteminstance_matching.py`

**Interfaces:**
- Produces:
  `_irg_match_grade_items(items: list[dict], activity_id: int) -> list[tuple[int, dict]]`.
- Sobrescribe:
  `_grades_by_type(entry, map_lines, grading_scale) -> dict`.

- [ ] **Step 1: Implementar el resolvedor mínimo**

```python
@staticmethod
def _irg_match_grade_items(items, activity_id):
    return [
        (index, item)
        for index, item in enumerate(items)
        if activity_id in (
            item.get("id"),
            item.get("cmid"),
            item.get("iteminstance"),
        )
    ]
```

La enumeración garantiza que un mismo item se incluye una sola vez aunque dos
campos compartan el mismo valor.

- [ ] **Step 2: Sobrescribir `_grades_by_type`**

Conservar agregación, escala, validación de tipo y detección de reutilización
del addon base, sustituyendo exclusivamente la obtención de candidatos por
`_irg_match_grade_items`.

Para cero candidatos usar:

```python
_("No se encontró la actividad Moodle %s por id/cmid/iteminstance.")
```

Para más de uno usar:

```python
_(
    "La actividad Moodle %s tiene una resolución ambigua "
    "(%s coincidencias por id/cmid/iteminstance)."
)
```

- [ ] **Step 3: Añadir pruebas de resolución funcional**

Cubrir nota por `iteminstance`, compatibilidad por `id` y `cmid`, tipo
incorrecto, colisión entre items y reutilización del mismo grade item.

- [ ] **Step 4: Ejecutar GREEN del resolvedor**

Run: suite completa del addon nuevo.

Expected: todos los casos pasan y el error de cero coincidencias ya no usa la
palabra «ambigua».

### Task 4: Integrar el resolvedor con múltiples HomeClass

**Files:**
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/wizard/moodle_sync_wizard.py`
- Modify: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/tests/test_iteminstance_matching.py`

**Interfaces:**
- Sobrescribe:
  `_irg_resolution_conflict(entry, map_lines) -> str | False`.
- Consume: `_irg_match_grade_items`.

- [ ] **Step 1: Añadir pruebas RED de HomeClass**

Crear dos cursos candidatos. En el primero, el usuario existe pero la actividad
no; en el segundo, el grade item contiene:

```python
{
    "id": 555,
    "cmid": 3290,
    "iteminstance": 205,
    "itemmodule": "quiz",
    "graderaw": 8.0,
    "grademax": 10.0,
}
```

Comprobar que el wizard selecciona el segundo curso y genera una línea válida
con nota `8.0`.

- [ ] **Step 2: Ejecutar RED de HomeClass**

Run: suite del addon nuevo filtrada por el caso HomeClass.

Expected: el primer curso se descarta, pero el segundo aún no resuelve
`iteminstance`.

- [ ] **Step 3: Sobrescribir `_irg_resolution_conflict`**

Reutilizar `_irg_match_grade_items`. Cero candidatos devuelve `False` para que
el fallback continúe; más de uno, tipo incompatible o reutilización devuelve el
mensaje bloqueante correspondiente.

- [ ] **Step 4: Ejecutar GREEN de HomeClass**

Run: suite completa del addon nuevo.

Expected: el segundo curso queda seleccionado y no aparece incompatibilidad.

### Task 5: Review, validación y documentación

**Files:**
- Create: `addons-extra/extrairg/irg_gradebook_moodle_iteminstance/README.rst`
- Create: `missions/fix-gradebook-moodle-iteminstance-matching/verification.json`
- Create: `missions/fix-gradebook-moodle-iteminstance-matching/CHANGELOG.md`
- Create: `missions/fix-gradebook-moodle-iteminstance-matching/artifacts/review.txt`
- Create: `missions/fix-gradebook-moodle-iteminstance-matching/artifacts/validation-tests.txt`
- Modify when reusable knowledge changes:
  `.agents/knowledge/odoo_development_modding/artifacts/irg_gradebook_moodle_course_activity_routing.md`

**Interfaces:**
- Produces: gate de review sin bloqueantes y `verification.json` con
  `status: passed`.

- [ ] **Step 1: Ejecutar review independiente**

El revisor compara código y pruebas con esta especificación, verifica que no se
modificaron addons existentes y deja su conclusión en `artifacts/review.txt`.

- [ ] **Step 2: Ejecutar validación independiente**

El validador ejecuta desde cero:

```bash
python3 -m compileall \
  addons-extra/extrairg/irg_gradebook_moodle_iteminstance

docker compose -f docker-compose.local.yml \
  -f missions/fix-gradebook-moodle-iteminstance-matching/docker-compose.worktree.yml \
  run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d irg_iteminstance_validation \
  -u irg_gradebook_moodle_routing,irg_gradebook_moodle_mapping_admin,irg_gradebook_moodle_homeclass_editions,irg_gradebook_moodle_iteminstance \
  --test-enable \
  --test-tags=/irg_gradebook_moodle_routing,/irg_gradebook_moodle_mapping_admin,/irg_gradebook_moodle_homeclass_editions,/irg_gradebook_moodle_iteminstance \
  --stop-after-init
```

Guardar comandos, entorno, conteos y cleanup de la base temporal.

- [ ] **Step 3: Crear `verification.json`**

Usar únicamente `pass`, `fail` o `skipped`; `status` será `passed` solo si no
hay fallos y todo skip está justificado.

- [ ] **Step 4: Documentar**

El README debe explicar los tres espacios de IDs, la deduplicación por item,
los errores y que no hace falta reimportar. Actualizar changelog y knowledge
solo con la decisión reutilizable.

- [ ] **Step 5: Comprobación final acotada**

Ejecutar `git diff --check`, revisar alcance con `git status --short` y confirmar
que documentación no alteró runtime. No hacer commit ni push.
