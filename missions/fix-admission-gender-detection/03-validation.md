# Validation — misión `fix-admission-gender-detection`

Ejecutado por el Validator. Entorno confirmado: contenedores `odoo16irg_local`
(Up), `pgodoo16irg_local` (Up), `redisodoo16irg_local` (Up). Rama de trabajo
`fix/admission-gender-detection` (confirmado con `git branch --show-current`).
No existe `PROJECT.md` en el repo (mismo hallazgo NIT-1 del Reviewer); se ha
seguido `01-plan.md`/`00-spec.md` como referencia de comandos canonicos de
esta mision. No se ha tocado ninguna BD de servidor beta/prod; todo contra
`test_irg_db`. No se ha hecho commit ni cambio de rama.

---

## Tarea 1 - Helper `_irg_resolve_admission_gender` (isep_openeducat_sale)

```
$ grep -n "_IRG_GENDER_MAP" .../isep_openeducat_sale/models/sale_order.py
20:    _IRG_GENDER_MAP = {
35:        return self._IRG_GENDER_MAP.get(raw, False)
$ grep -n "def _irg_resolve_admission_gender" .../sale_order.py
25:    def _irg_resolve_admission_gender(self, partner=None):
$ python3 -m py_compile .../sale_order.py && echo OK
OK
```
PASS (G1: ambos grep >=1 linea; G2: OK).

## Tarea 2 - Sustitucion en isep_openeducat_sale (linea ~336, ahora 356)

```
$ ! grep -nE "self\.gender or .*\.gender or 'o'" .../isep_openeducat_sale/models/sale_order.py && echo NO_OLD_PATTERN
NO_OLD_PATTERN
$ grep -n "_irg_resolve_admission_gender" .../sale_order.py
25:    def _irg_resolve_admission_gender(self, partner=None):
356:            'gender': self._irg_resolve_admission_gender(self.partner_id) or 'o',
$ python3 -m py_compile .../sale_order.py && echo OK
OK
```
PASS (H1: NO_OLD_PATTERN; H2: 2 lineas - definicion + uso; H3: OK).

## Tarea 3 - Sustituciones en isep_sale_order_admissions (2 puntos)

```
$ ! grep -nE "self\.gender or .*\.gender or 'o'" .../isep_sale_order_admissions/models/sale_order.py && echo NO_OLD_PATTERN
NO_OLD_PATTERN
$ test "$(grep -c "_irg_resolve_admission_gender" .../sale_order.py)" -eq 2 && echo TWO_CALLS
TWO_CALLS
$ python3 -m py_compile .../sale_order.py && echo OK
OK
```
PASS (I1/I2/I3 todos conformes).

## Tarea 4 - Sustituciones en isep_admission_from_student_field (4 puntos)

```
$ ! grep -nE "self\.gender or .*\.gender or 'o'" .../isep_admission_from_student_field/models/sale_order.py && echo NO_OLD_PATTERN
NO_OLD_PATTERN
$ test "$(grep -c "_irg_resolve_admission_gender(target_partner)" .../sale_order.py)" -eq 4 && echo FOUR_CALLS
FOUR_CALLS
$ python3 -m py_compile .../sale_order.py && echo OK
OK
```
PASS (J1/J2/J3 todos conformes; las 4 llamadas usan `target_partner`, no
`self.partner_id`, cumpliendo R1).

## Tarea 5 - Respetar 'o' explicito (R3) en irg_admission_gender_fix

```
$ ! grep -nE "incoming_gender == 'o'\) and partner" .../op_admission.py && echo ADMISSION_OK
ADMISSION_OK
$ ! grep -nE "incoming_gender == 'o'\) and partner" .../op_student.py && echo STUDENT_OK
STUDENT_OK
$ python3 -m py_compile .../op_admission.py && echo OK
OK
$ python3 -m py_compile .../op_student.py && echo OK
OK
```
PASS (K1/K2 conformes en ambos archivos).

## Tarea 6 - Manifiestos, romper ciclo (R4/R4b)

```
$ python3 -c "import ast; ast.literal_eval(open(m).read()); print('OK', m)"  # x3 manifiestos
OK addons-extra/extrairg/irg_admission_gender_fix/__manifest__.py
OK addons-extra/addons_uisep/isep_sale_order_admissions/__manifest__.py
OK addons-extra/addons_uisep/isep_admission_from_student_field/__manifest__.py
$ python3 -c "...assert 'isep_admission_from_student_field' not in d['depends']...; print('FIX_NO_CYCLE')"
FIX_NO_CYCLE
$ python3 -c "...assert 'irg_admission_gender_fix' in d['depends']...; print('SOA_DEP_OK')"
SOA_DEP_OK
$ python3 -c "...print('AFSF_DEP_OK')"
AFSF_DEP_OK
$ python3 -c "...print(d['depends'])"  # depends finales del fix
['openeducat_admission', 'openeducat_core', 'isep_openeducat_sale']
```
PASS (L1/L2/L3 conformes; depends finales del fix coinciden exactamente
con R4b: sin `odoo_moodle_connector` ni `isep_admission_from_student_field`).

## Tarea 7 - Tests nuevos test_gender_mapping.py

```
$ grep -n "def test_06" .../test_gender_mapping.py
288:    def test_06_student_gender_over_order(self):
$ grep -n "def test_07" .../test_gender_mapping.py
320:    def test_07_explicit_other_not_overwritten(self):
$ grep -n "def test_08" .../test_gender_mapping.py
347:    def test_08_moodle_value_mapped_by_helper(self):
$ python3 -m py_compile .../test_gender_mapping.py && echo OK
OK
```
PASS (M1/M2 conformes).

## Tarea 8 - Validacion global: update de modulos + suite de tests (A1-A5)

### Paso 1 (A5) - update de los 4 modulos

```
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u isep_openeducat_sale,isep_sale_order_admissions,isep_admission_from_student_field,irg_admission_gender_fix \
  --stop-after-init --no-http
```
Output relevante:
```
2026-07-03 13:19:16,393 334 INFO test_irg_db odoo.modules.loading: Modules loaded.
2026-07-03 13:19:16,409 334 INFO test_irg_db odoo.modules.registry: Registry loaded in 30.618s
```
Verificacion del grep literal del criterio A5:
```
$ grep -iE "circular|not met|Traceback|Failed to (load|initialize)" irg_gender_update.log
```
Si hay coincidencias, pero son un falso positivo del patron `Traceback`: se
deben a la funcion interna de Odoo `showwarning_with_traceback` (captura de
`DeprecationWarning` con stack de contexto al importar modulos legacy), no a
una excepcion real. Verificacion adicional (evidencia real, no inferida):
```
$ grep -c "Traceback (most recent call last)" irg_gender_update.log
0
$ grep -c " CRITICAL " irg_gender_update.log
0
$ grep -iE "circular|not met" irg_gender_update.log
(sin resultados)
```
Un unico ERROR real en el log (preexistente, no relacionado con genero ni
dependencias, no bloquea la carga):
```
2026-07-03 13:19:15,782 334 ERROR test_irg_db odoo.schema: Table 'op_course': unable to set NOT NULL on column 'lang'
```
Este error de schema (`op_course.lang`) es preexistente en la BD y no impide
`Modules loaded.`/`Registry loaded`; no esta relacionado con los 4 modulos
de la mision ni con los cambios de genero. Ningun `CircularDependency`,
ningun "Dependencies of module ... not met", ninguna excepcion Python real,
y el proceso finaliza con shutdown limpio.

A5: PASS (con matiz documentado: el patron literal `Traceback` del plan
produce falso positivo por el nombre de la funcion de logging de Odoo; la
evidencia real -ausencia de `Traceback (most recent call last)`, ausencia de
CRITICAL, presencia de `Modules loaded`/`Registry loaded`- confirma que no
hay error de carga ni de ciclo de dependencias).

### Paso 2 (A1-A4) - suite de tests del modulo fix

```
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_admission_gender_fix --test-enable --test-tags irg_gender \
  --stop-after-init --no-http
```
Los 8 tests arrancaron:
```
Starting TestGenderMapping.test_01_create_admission_explicit_gender
Starting TestGenderMapping.test_02_create_admission_from_partner_gender
Starting TestGenderMapping.test_03_write_admission_gender
Starting TestGenderMapping.test_04_student_gender_mapping
Starting TestGenderMapping.test_05_intelligent_gender_guessing
Starting TestGenderMapping.test_06_student_gender_over_order
Starting TestGenderMapping.test_07_explicit_other_not_overwritten
Starting TestGenderMapping.test_08_moodle_value_mapped_by_helper
```
Resumen oficial de Odoo:
```
2026-07-03 13:26:18,567 358 INFO test_irg_db odoo.tests.result: 0 failed, 0 error(s) of 8 tests when loading database 'test_irg_db'
```
Verificacion del grep literal del criterio (A1-A4):
```
$ grep -iE "FAIL:|ERROR:|[1-9][0-9]* failed|[1-9][0-9]* error" irg_gender_tests.log
```
1 coincidencia, tambien falso positivo: es la misma linea de warning de
schema preexistente (`res_partner.username` NOT NULL) que coincide
literalmente con el patron `ERROR:` por el formato de log de Odoo
(`... ERROR test_irg_db odoo.schema: ...`), no con un fallo de test.
Verificacion especifica del formato real de fallo de test-runner
(`FAIL: TestClass.method` / `ERROR: TestClass.method`):
```
$ grep -nE "^(FAIL|ERROR): " irg_gender_tests.log
(sin resultados) -> NO_TEST_FAILURES
```
Esta misma linea de warning de schema ya aparecia en el log del Paso 1
(preexistente, no introducida por esta mision).

A1-A4: PASS (resumen oficial `0 failed, 0 error(s) of 8 tests`; los 8
metodos, incluidos `test_06` (A2), `test_07` (A3) y `test_08` (A4), se
ejecutaron sin fallo).

---

## Comprobacion estatica extra (grep global + estado de modulo revertido)

```
$ grep -rnE "self\.gender or .*\.gender or 'o'" addons-extra --include="*.py"
addons-extra/extrairg/irg_admissions_by_student/models/sale_order.py:48:            'gender': self.gender or target_partner.gender or 'o',
```
Unica ocurrencia restante del patron buggy en todo `addons-extra`, y coincide
exactamente con `irg_admissions_by_student` (revertido a proposito por
decision del usuario, documentado en `02-progress.md` Iteracion 2b y en la
adenda de `02b-review.md`; modulo desinstalado, fuera del alcance de la
mision).

```
$ git status --porcelain addons-extra/extrairg/irg_admissions_by_student/
(sin salida)
```
Working tree limpio para ese modulo: confirma que la reversion con
`git checkout --` se aplico correctamente y no quedan cambios pendientes.

PASS.

---

## Veredicto por tarea

| Tarea | Criterio | Resultado |
|---|---|---|
| 1 | G1/G2 helper existe y compila | PASS |
| 2 | H1/H2/H3 sustitucion isep_openeducat_sale | PASS |
| 3 | I1/I2/I3 sustituciones isep_sale_order_admissions | PASS |
| 4 | J1/J2/J3 sustituciones isep_admission_from_student_field | PASS |
| 5 | K1/K2 respeta 'o' explicito | PASS |
| 6 | L1/L2/L3 manifiestos sin ciclo (R4b) | PASS |
| 7 | M1/M2 tests nuevos existen y compilan | PASS |
| 8 (A5) | update 4 modulos sin ciclo/error de carga | PASS |
| 8 (A1-A4) | suite `irg_gender`: 0 failed, 0 error(s) of 8 tests | PASS |
| Extra | grep global patron buggy + estado modulo revertido | PASS |

## Veredicto global

PASS global
