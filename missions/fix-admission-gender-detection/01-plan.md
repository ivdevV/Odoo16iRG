# Plan — misión `fix-admission-gender-detection`

Derivado de `00-spec.md` (aprobada). El Planner ha verificado con lectura directa
que los 7 puntos de sustitución siguen siendo válidos y ha detectado un matiz de
diseño respecto a R3 (ver Tarea 5). No se escribe código aquí: solo el plan.

## Entorno de verificación (referencia para todas las tareas)

- Repo raíz: `/Users/ivrogo/Workspace/Proyectos iRG/Odoo16iRG`
- Contenedor Odoo: `odoo16irg_local` (compose `docker-compose.local.yml`).
  Los addons se montan **read-only** en `/mnt/extra-addons`.
- Contenedor Postgres: `pgodoo16irg_local`. BD de pruebas: `test_irg_db`.
- Rama de trabajo: `fix/admission-gender-detection` creada desde `Dev_iRG`
  (NUNCA desde `main`). El Coder debe verificar/crear la rama antes de tocar código.
- Módulos afectados (rutas absolutas):
  - `addons-extra/addons_uisep/isep_openeducat_sale/`
  - `addons-extra/addons_uisep/isep_sale_order_admissions/`
  - `addons-extra/addons_uisep/isep_admission_from_student_field/`
  - `addons-extra/extrairg/irg_admission_gender_fix/`

### Comandos base reutilizables

Sintaxis Python válida (para tareas de edición de `.py`):
```bash
docker exec odoo16irg_local python3 -m py_compile "<ruta_dentro_del_contenedor>"
```
(los addons están en `/mnt/extra-addons/...`; el path relativo desde `addons-extra`
se mantiene, p.ej. `/mnt/extra-addons/addons_uisep/isep_openeducat_sale/models/sale_order.py`).

Manifiesto es dict Python válido:
```bash
python3 -c "import ast; ast.literal_eval(open('<manifest>').read()); print('OK')"
```

Update + tests de un módulo en `test_irg_db` (Odoo 16, patrón del repo):
```bash
docker exec odoo16irg_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_db \
  -u <lista_modulos> --test-enable --test-tags <tags> \
  --stop-after-init --no-http
```
> Nota entorno: los addons están montados `:ro`; el update lee los `.py` del host en
> caliente. Si el daemon local no expone Docker, el Validator lo documentará como
> N/A siguiendo la práctica del repo, pero A1–A5 **exigen** ejecución real cuando
> Docker esté disponible (que es el caso objetivo de esta misión).

---

## Tarea 1 — Helper compartido `_irg_resolve_admission_gender` en `isep_openeducat_sale`

**Descripción.** En `addons-extra/addons_uisep/isep_openeducat_sale/models/sale_order.py`
(clase `SaleOrder(_inherit='sale.order')`, definida desde la línea 14) añadir:
- constante de clase `_IRG_GENDER_MAP` = `{'m':'m','f':'f','o':'o','male':'m','female':'f','not-sure':'o'}`.
- método `_irg_resolve_admission_gender(self, partner=None)` con la firma y semántica
  del diseño aprobado (spec §"Helper de referencia"): estudiante primero
  (`partner or self.partner_id`), pedido (`self.gender`) como fallback, `False` si
  el valor crudo no está en el mapa.

Este es el **único** sitio donde se define el helper; los demás módulos lo heredan por
ser todos `_inherit='sale.order'` (herencia de modelo, no de clase Python), por lo que
`self._irg_resolve_admission_gender(...)` está disponible en cualquier `sale.order`
siempre que `isep_openeducat_sale` esté en el grafo de dependencias (lo está: es
dependencia directa o transitiva de los tres módulos de admisión).

**Criterio de aceptación.**
```bash
# G1: el método y la constante existen en el archivo
grep -n "_IRG_GENDER_MAP" addons-extra/addons_uisep/isep_openeducat_sale/models/sale_order.py
grep -n "def _irg_resolve_admission_gender" addons-extra/addons_uisep/isep_openeducat_sale/models/sale_order.py
# G2: compila
docker exec odoo16irg_local python3 -m py_compile \
  /mnt/extra-addons/addons_uisep/isep_openeducat_sale/models/sale_order.py && echo OK
```
Pasa si ambos `grep` devuelven ≥1 línea y `py_compile` imprime `OK`.
Verificación funcional definitiva del mapeo/prioridad: cubierta por A2/A4 en Tarea 8.

**Dependencias.** Ninguna (primera tarea). Todas las sustituciones (Tareas 2–4)
dependen de ésta.

---

## Tarea 2 — Sustitución en `isep_openeducat_sale` (1 punto)

**Descripción.** En el mismo archivo de la Tarea 1, línea **336** (verificada), dentro
del `op_admission.create({...})`, reemplazar:
```python
'gender': self.gender or self.partner_id.gender or 'o',
```
por una llamada al helper que use el partner de la admisión (`self.partner_id`):
```python
'gender': self._irg_resolve_admission_gender(self.partner_id) or 'o',
```
El sufijo `or 'o'` se mantiene como red de seguridad de valor NOT NULL; el fix (Tarea 5)
sólo adivinará cuando llegue `False`/vacío, no cuando llegue `'o'` explícito.

**Criterio de aceptación.**
```bash
# H1: ya no queda el patrón antiguo "self.gender or ... .gender or 'o'" en este archivo
! grep -nE "self\.gender or .*\.gender or 'o'" \
  addons-extra/addons_uisep/isep_openeducat_sale/models/sale_order.py && echo NO_OLD_PATTERN
# H2: existe al menos una llamada al helper
grep -n "_irg_resolve_admission_gender" \
  addons-extra/addons_uisep/isep_openeducat_sale/models/sale_order.py
# H3: compila
docker exec odoo16irg_local python3 -m py_compile \
  /mnt/extra-addons/addons_uisep/isep_openeducat_sale/models/sale_order.py && echo OK
```
Pasa si H1 imprime `NO_OLD_PATTERN`, H2 devuelve ≥2 líneas (definición + uso) y H3 `OK`.

**Dependencias.** Tarea 1.

---

## Tarea 3 — Sustituciones en `isep_sale_order_admissions` (2 puntos)

**Descripción.** En `addons-extra/addons_uisep/isep_sale_order_admissions/models/sale_order.py`,
reemplazar los 2 puntos verificados por el helper, usando en cada caso el partner de la
admisión correspondiente:
- línea **124** (dentro de `create` de `op.admission`, variable local `partner`):
  `'gender': self.gender or partner.gender or 'o',` →
  `'gender': self._irg_resolve_admission_gender(partner) or 'o',`
- línea **273** (`op_admission.create`, usa `self.partner_id`):
  `'gender': self.gender or self.partner_id.gender or 'o',` →
  `'gender': self._irg_resolve_admission_gender(self.partner_id) or 'o',`

**Criterio de aceptación.**
```bash
# I1: no quedan patrones antiguos
! grep -nE "self\.gender or .*\.gender or 'o'" \
  addons-extra/addons_uisep/isep_sale_order_admissions/models/sale_order.py && echo NO_OLD_PATTERN
# I2: exactamente 2 llamadas al helper
test "$(grep -c "_irg_resolve_admission_gender" \
  addons-extra/addons_uisep/isep_sale_order_admissions/models/sale_order.py)" -eq 2 && echo TWO_CALLS
# I3: compila
docker exec odoo16irg_local python3 -m py_compile \
  /mnt/extra-addons/addons_uisep/isep_sale_order_admissions/models/sale_order.py && echo OK
```
Pasa si I1 → `NO_OLD_PATTERN`, I2 → `TWO_CALLS`, I3 → `OK`.

**Dependencias.** Tarea 1.

---

## Tarea 4 — Sustituciones en `isep_admission_from_student_field` (4 puntos)

**Descripción.** En `addons-extra/addons_uisep/isep_admission_from_student_field/models/sale_order.py`
reemplazar los 4 puntos verificados. Aquí el partner del estudiante es `target_partner`,
NO `self.partner_id` (el módulo distingue titular/pagador vs alumno). Por tanto **hay que
pasar `target_partner` explícitamente** para respetar R1:
- línea **106** (`op.admission` write/create, `target_partner`):
  → `'gender': self._irg_resolve_admission_gender(target_partner) or 'o',`
- línea **127** (`op.student.create`, `target_partner`):
  → `'gender': self._irg_resolve_admission_gender(target_partner) or 'o',`
- línea **157** (`op.admission.create`, `target_partner`):
  → `'gender': self._irg_resolve_admission_gender(target_partner) or 'o',`
- línea **222** (`op_admission.create`, `target_partner`):
  → `'gender': self._irg_resolve_admission_gender(target_partner) or 'o',`

**Nota crítica de corrección (R1):** en este módulo NO usar el partner por defecto del
helper (`self.partner_id`), porque `self.partner_id` es el titular del pedido y
`target_partner` es el alumno. Pasar siempre `target_partner`.

**Criterio de aceptación.**
```bash
# J1: no quedan patrones antiguos
! grep -nE "self\.gender or .*\.gender or 'o'" \
  addons-extra/addons_uisep/isep_admission_from_student_field/models/sale_order.py && echo NO_OLD_PATTERN
# J2: exactamente 4 llamadas al helper, todas con target_partner
test "$(grep -c "_irg_resolve_admission_gender(target_partner)" \
  addons-extra/addons_uisep/isep_admission_from_student_field/models/sale_order.py)" -eq 4 && echo FOUR_CALLS
# J3: compila
docker exec odoo16irg_local python3 -m py_compile \
  /mnt/extra-addons/addons_uisep/isep_admission_from_student_field/models/sale_order.py && echo OK
```
Pasa si J1 → `NO_OLD_PATTERN`, J2 → `FOUR_CALLS`, J3 → `OK`.

**Dependencias.** Tarea 1.

---

## Tarea 5 — Respetar `'o'` explícito en `irg_admission_gender_fix` (R3)

**Descripción.** Corregir `create()`/`write()` en ambos modelos del fix para que un
`'o'` **entrante e informado** NO sea sobreescrito por la adivinación por nombre/título.
Estado actual verificado (viola R3):

- `op_admission.py` línea 122: `elif (not incoming_gender or incoming_gender == 'o') and partner:`
  → trata `'o'` como "sin informar" y adivina. Debe cambiarse para que **`'o'` explícito
  se conserve** y sólo se adivine cuando el género llega vacío/`False`.
- `op_student.py` línea 122: idéntico problema, mismo cambio.

Cambio requerido (ambos archivos, en `create`):
1. Mantener el mapeo de `'male'/'female'/'not-sure'` → `'m'/'f'/'o'` (ya correcto).
2. La rama de adivinación por partner debe dispararse **sólo** cuando
   `not incoming_gender` (vacío/`False`), NO cuando `incoming_gender == 'o'`.
3. Cuando `incoming_gender == 'o'` (o mapeado a `'o'` desde `'not-sure'/'other'`), fijar
   `vals['gender'] = 'o'` y no adivinar.

En `write()` la lógica ya respeta `'o'` (sólo actúa si `incoming_gender` es truthy o si
cambia `partner_id` sin gender). Verificar que un `write({'gender':'o'})` deje `'o'`; si
la lógica actual ya lo cumple, no tocar `write` salvo para consistencia.

**Criterio de aceptación.**
```bash
# K1: ya NO existe la condición que adivina sobre 'o' entrante
! grep -nE "incoming_gender == 'o'\) and partner" \
  addons-extra/extrairg/irg_admission_gender_fix/models/op_admission.py && echo ADMISSION_OK
! grep -nE "incoming_gender == 'o'\) and partner" \
  addons-extra/extrairg/irg_admission_gender_fix/models/op_student.py && echo STUDENT_OK
# K2: compilan
docker exec odoo16irg_local python3 -m py_compile \
  /mnt/extra-addons/extrairg/irg_admission_gender_fix/models/op_admission.py && echo OK
docker exec odoo16irg_local python3 -m py_compile \
  /mnt/extra-addons/extrairg/irg_admission_gender_fix/models/op_student.py && echo OK
```
Verificación funcional definitiva (`'o'` explícito no se sobreescribe): test A3 en Tarea 8.

**Dependencias.** Independiente de Tareas 1–4 en cuanto a edición, pero conceptualmente
cierra el circuito con el helper (helper devuelve `'o'` cuando el partner tiene `'o'`,
y el fix debe respetarlo). Debe estar antes de la ejecución de tests (Tarea 8).

---

## Tarea 6 — Romper el ciclo de dependencias en manifiestos (R4)

**Descripción.** Estado verificado de `depends`:
- `irg_admission_gender_fix/__manifest__.py`: depende de
  `['openeducat_admission','openeducat_core','isep_openeducat_sale',
  'isep_admission_from_student_field','odoo_moodle_connector']`.
- `isep_sale_order_admissions/__manifest__.py`: NO depende del fix.
- `isep_admission_from_student_field/__manifest__.py`: NO depende del fix.

Cambios (evitando ciclo):
1. En `irg_admission_gender_fix/__manifest__.py`: **quitar**
   `'isep_admission_from_student_field'` de `depends` (el fix no referencia nada de ese
   módulo; sólo inherita `op.admission`/`op.student`/`res.partner`). Se puede mantener
   `isep_openeducat_sale` (necesario para que el helper esté en el grafo) y
   `odoo_moodle_connector` (define los valores Moodle del selection).
2. En `isep_sale_order_admissions/__manifest__.py`: **añadir**
   `'irg_admission_gender_fix'` a `depends`.
3. En `isep_admission_from_student_field/__manifest__.py`: **añadir**
   `'irg_admission_gender_fix'` a `depends`.

Con esto la dirección del grafo queda:
`irg_admission_gender_fix` → `isep_openeducat_sale` (helper) y ambos módulos de admisión
→ `irg_admission_gender_fix`. No hay ciclo porque el fix ya no apunta a
`isep_admission_from_student_field`.

**Criterio de aceptación.**
```bash
# L1: los tres manifiestos son dict Python válidos
for m in \
  addons-extra/extrairg/irg_admission_gender_fix/__manifest__.py \
  addons-extra/addons_uisep/isep_sale_order_admissions/__manifest__.py \
  addons-extra/addons_uisep/isep_admission_from_student_field/__manifest__.py; do
  python3 -c "import ast; ast.literal_eval(open('$m').read()); print('OK $m')"
done
# L2: el fix ya NO depende de isep_admission_from_student_field
python3 -c "import ast; d=ast.literal_eval(open('addons-extra/extrairg/irg_admission_gender_fix/__manifest__.py').read()); assert 'isep_admission_from_student_field' not in d['depends'], d['depends']; print('FIX_NO_CYCLE')"
# L3: ambos módulos de admisión SÍ dependen del fix
python3 -c "import ast; d=ast.literal_eval(open('addons-extra/addons_uisep/isep_sale_order_admissions/__manifest__.py').read()); assert 'irg_admission_gender_fix' in d['depends'], d['depends']; print('SOA_DEP_OK')"
python3 -c "import ast; d=ast.literal_eval(open('addons-extra/addons_uisep/isep_admission_from_student_field/__manifest__.py').read()); assert 'irg_admission_gender_fix' in d['depends'], d['depends']; print('AFSF_DEP_OK')"
```
Pasa si L1 imprime 3× `OK`, L2 → `FIX_NO_CYCLE`, L3 → `SOA_DEP_OK` y `AFSF_DEP_OK`.
La ausencia real de ciclo se confirma de forma definitiva por el `-u` sin error en
Tarea 8 (criterio A5).

**Dependencias.** Independiente de las ediciones de código; debe estar antes de la
ejecución de tests (Tarea 8), porque el update `-u` de los 4 módulos usa este grafo.

---

## Tarea 7 — Tests nuevos en `irg_admission_gender_fix/tests/test_gender_mapping.py`

**Descripción.** Añadir tests que cubran A2, A3 y A4 al archivo existente (que ya tiene
`test_01`–`test_05`). Reutilizar los fixtures de `setUp` (course/register/batch/fees_term).
Casos mínimos:

- **`test_06_student_gender_over_order` (A2):** simular la prioridad estudiante>pedido.
  Como el helper vive en `sale.order`, el test puede ejercitarlo de dos formas
  (el Coder elige la más robusta en este entorno):
  (a) crear un `sale.order` con `gender='m'` y un `partner_id`/`target_partner` cuyo
  partner tenga `gender='f'`, invocar `order._irg_resolve_admission_gender(partner_f)` y
  aseverar `== 'f'`; **o**
  (b) test de integración: crear admisión con `partner` (alumno) género `f` mientras el
  valor del pedido sería `m`, y aseverar `admission.gender == 'f'`.
  Requisito de aceptación del test: demuestra que **el género del estudiante gana**.
- **`test_07_explicit_other_not_overwritten` (A3):** crear `op.admission` con
  `gender='o'` explícito y `partner` cuyo nombre adivinaría `m`/`f` (p.ej. "Laura Gomez"),
  aseverar `admission.gender == 'o'`. Repetir en `write`: `admission.write({'gender':'o'})`
  → sigue `'o'`.
- **`test_08_moodle_value_mapped_by_helper` (A4):** partner con `gender='female'`
  (valor Moodle); resolver vía helper `order._irg_resolve_admission_gender(partner)`
  → `'f'`, demostrando que el mapeo ocurre en el helper (no depende de la intercepción
  del fix). Complementariamente, crear admisión y aseverar `'f'`.

Los tests deben quedar bajo un tag ejecutable de forma aislada. Usar el patrón estándar
Odoo: decorar la clase o añadir `@tagged('irg_gender')` (import `from odoo.tests import tagged`),
manteniendo compatibilidad con la ejecución por módulo. Documentar en el propio archivo
el tag elegido para que Tarea 8 lo use.

**Criterio de aceptación.**
```bash
# M1: existen los tres nuevos métodos
grep -n "def test_06" addons-extra/extrairg/irg_admission_gender_fix/tests/test_gender_mapping.py
grep -n "def test_07" addons-extra/extrairg/irg_admission_gender_fix/tests/test_gender_mapping.py
grep -n "def test_08" addons-extra/extrairg/irg_admission_gender_fix/tests/test_gender_mapping.py
# M2: el archivo compila
docker exec odoo16irg_local python3 -m py_compile \
  /mnt/extra-addons/extrairg/irg_admission_gender_fix/tests/test_gender_mapping.py && echo OK
```
Pasa si M1 devuelve las tres líneas y M2 → `OK`. La ejecución real (verde) es Tarea 8.

**Dependencias.** Tareas 1–6 (los tests aseveran el comportamiento resultante de todas
ellas).

---

## Tarea 8 — Validación global: update de módulos + suite de tests (A1–A5)

**Descripción.** Ejecutar el update de los 4 módulos y la suite de tests contra
`test_irg_db` en el contenedor, capturando output real. Cubre A1 (tests existentes +
nuevos en verde), A2/A3/A4 (los tests nuevos pasan) y A5 (update sin error de ciclo).

**Comandos exactos.**
```bash
# Paso 1 (A5): update de los cuatro módulos, debe terminar sin error de dependencias
docker exec odoo16irg_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_db \
  -u isep_openeducat_sale,isep_sale_order_admissions,isep_admission_from_student_field,irg_admission_gender_fix \
  --stop-after-init --no-http 2>&1 | tee /tmp/irg_gender_update.log

# Paso 2 (A1–A4): ejecutar la suite de tests del módulo fix
docker exec odoo16irg_local odoo \
  -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_admission_gender_fix --test-enable \
  --test-tags /irg_admission_gender_fix \
  --stop-after-init --no-http 2>&1 | tee /tmp/irg_gender_tests.log
```
> Si en Tarea 7 se usó un tag propio (p.ej. `irg_gender`), el Paso 2 puede acotarse con
> `--test-tags irg_gender`. La forma `/irg_admission_gender_fix` limita a los tests del
> módulo. El Validator debe usar el tag que el archivo de tests declare.

**Criterio de aceptación (binario).**
- **A5:** el log del Paso 1 NO contiene `CircularDependency` ni
  `Dependencies of module ... not met` ni traceback de error de carga; y contiene
  la línea de módulos cargados/actualizados sin abortar. Verificación:
  ```bash
  ! grep -iE "circular|not met|Traceback|Failed to (load|initialize)" /tmp/irg_gender_update.log && echo A5_PASS
  ```
- **A1–A4:** el log del Paso 2 reporta `0 failed, 0 error` (patrón estándar Odoo 16
  `X failed, Y error(s)`), incluyendo `test_01`–`test_08`. Verificación:
  ```bash
  grep -E "tests?.*(failed|error)" /tmp/irg_gender_tests.log
  ! grep -iE "FAIL:|ERROR:|[1-9][0-9]* failed|[1-9][0-9]* error" /tmp/irg_gender_tests.log && echo TESTS_PASS
  ```
  Pasa si aparece el resumen con 0 fallos/0 errores y el `grep` de fallos no encuentra
  coincidencias positivas.

**Dependencias.** Todas las anteriores (1–7).

---

## Orden de ejecución y grafo de dependencias

```
Tarea 1 (helper)
  ├─> Tarea 2 (isep_openeducat_sale: 1 punto)
  ├─> Tarea 3 (isep_sale_order_admissions: 2 puntos)
  └─> Tarea 4 (isep_admission_from_student_field: 4 puntos, target_partner)

Tarea 5 (fix: respetar 'o' explícito)      ─┐
Tarea 6 (manifiestos: romper ciclo)        ─┤
Tarea 7 (tests nuevos A2/A3/A4)  (necesita 1–6) ─┤
                                                └─> Tarea 8 (update + suite: A1–A5)
```
Orden lineal recomendado para el Coder: **1 → 2 → 3 → 4 → 5 → 6 → 7 → 8.**
Tareas 5 y 6 pueden hacerse en cualquier orden entre 4 y 7; se listan así por claridad.

## Mapa criterios globales de la spec → tareas

| Criterio spec | Cubierto por |
|---|---|
| A1 (suite en verde) | Tarea 8 Paso 2 |
| A2 (estudiante gana al pedido) | Tarea 1 (helper) + Tarea 7 test_06 + Tarea 8 |
| A3 (`'o'` explícito no se sobreescribe) | Tarea 5 + Tarea 7 test_07 + Tarea 8 |
| A4 (valor Moodle mapeado por helper) | Tarea 1 + Tarea 7 test_08 + Tarea 8 |
| A5 (update sin ciclo) | Tarea 6 + Tarea 8 Paso 1 |
| R1 (prioridad estudiante) | Tareas 1–4 (partner explícito, `target_partner` en Tarea 4) |
| R2 (mapeo en helper) | Tarea 1 |
| R3 (respetar `'o'`) | Tarea 5 |
| R4 (dependencias sin ciclo) | Tarea 6 |

## Notas para el Coder (no reexplorar, ya verificado por el Planner)

- Líneas confirmadas a fecha de este plan: `isep_openeducat_sale` 336;
  `isep_sale_order_admissions` 124 y 273; `isep_admission_from_student_field`
  106, 127, 157, 222. Si el editor las desplaza, usar el patrón
  `self.gender or <partner>.gender or 'o'` como ancla (es único por archivo salvo en
  `isep_admission_from_student_field`, donde aparece 4 veces).
- En `isep_admission_from_student_field` el partner del alumno es **`target_partner`**,
  no `self.partner_id`. No usar el default del helper ahí.
- El fix actual (op_admission.py / op_student.py, línea 122) trata `'o'` entrante como
  "sin informar" y adivina: ESE es el comportamiento que Tarea 5 debe eliminar.
- No tocar la BD del servidor beta/prod. Todo contra `test_irg_db` en `odoo16irg_local`.
- No hacer merge a `main`; al cerrar con PASS global, commit + push de
  `fix/admission-gender-detection` + PR contra `main`.
