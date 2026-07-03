# Progress — misión `fix-admission-gender-detection`

Estado: todas las tareas del plan (1-8) implementadas y verificadas localmente
por el Coder (sanity check). El Validator debe re-ejecutar y reportar
formalmente.

## Tarea 1 — Helper `_irg_resolve_admission_gender` (isep_openeducat_sale)

Archivo: `addons-extra/addons_uisep/isep_openeducat_sale/models/sale_order.py`

Añadidos en la clase `SaleOrder(_inherit='sale.order')`:
- `_IRG_GENDER_MAP = {'m':'m','f':'f','o':'o','male':'m','female':'f','not-sure':'o'}`
- `_irg_resolve_admission_gender(self, partner=None)`: `partner = partner or self.partner_id`;
  `raw = (partner and partner.gender) or self.gender`; `return self._IRG_GENDER_MAP.get(raw, False)`.

Verificado: `grep` de constante/método OK, `py_compile` en contenedor OK (usando
`cfile` a ruta escribible porque `/mnt/extra-addons` es `:ro` y no puede crear
`__pycache__`; ver nota de entorno más abajo).

## Tarea 2 — Sustitución en isep_openeducat_sale (1 punto, línea ~336)

`'gender': self.gender or self.partner_id.gender or 'o'` →
`'gender': self._irg_resolve_admission_gender(self.partner_id) or 'o'`.
Verificado: patrón antiguo ausente, helper presente, compila.

## Tarea 3 — Sustituciones en isep_sale_order_admissions (2 puntos)

Archivo: `addons-extra/addons_uisep/isep_sale_order_admissions/models/sale_order.py`
- Línea 124 (`_create_or_get_admission`, variable local `partner`):
  `self._irg_resolve_admission_gender(partner) or 'o'`.
- Línea 273 (`create_admission_manual`, `self.partner_id`):
  `self._irg_resolve_admission_gender(self.partner_id) or 'o'`.
Verificado: patrón antiguo ausente, 2 llamadas al helper, compila.

## Tarea 4 — Sustituciones en isep_admission_from_student_field (4 puntos)

Archivo: `addons-extra/addons_uisep/isep_admission_from_student_field/models/sale_order.py`
Las 4 ocurrencias (líneas 106, 127, 157, 222 antes de editar) usan
`self._irg_resolve_admission_gender(target_partner) or 'o'` (nunca
`self.partner_id`, por ser `target_partner` el alumno real, distinto del
titular del pedido — requisito R1).
Verificado: patrón antiguo ausente, 4 llamadas con `target_partner`, compila.

## Tarea 5 — Respetar 'o' explícito (R3) en irg_admission_gender_fix

Archivos: `models/op_admission.py` y `models/op_student.py` (idénticos en esta
lógica). Cambio en `create()`:
- Antes: `elif (not incoming_gender or incoming_gender == 'o') and partner:` →
  adivinaba también cuando llegaba `'o'` explícito.
- Ahora: el branch `incoming_gender in ('other','not-sure','Other','Otro')`
  fija `vals['gender'] = 'o'` y NO cae al `elif` de adivinación; el `elif` de
  adivinación quedó como `elif not incoming_gender and partner:` (solo
  vacío/False dispara la adivinación).
`write()` no se tocó: ya respetaba `'o'` (solo actúa si `incoming_gender` es
truthy y mapeable, o si cambia `partner_id` sin `gender` en el vals).
Verificado: patrón `incoming_gender == 'o') and partner` ausente en ambos
archivos, ambos compilan.

## Tarea 6 — Manifiestos, romper ciclo (R4) — CON CORRECCIÓN por cambio de requisito

Cambios iniciales:
- `irg_admission_gender_fix/__manifest__.py`: quitado
  `'isep_admission_from_student_field'` de `depends`.
- `isep_sale_order_admissions/__manifest__.py`: añadido
  `'irg_admission_gender_fix'`.
- `isep_admission_from_student_field/__manifest__.py`: añadido
  `'irg_admission_gender_fix'`.

**Corrección a mitad de misión (mensaje del orquestador):** el usuario aclaró
que producción NO usa `odoo_moodle_connector`; se actualizó `00-spec.md` con
R4b. Se quitó TAMBIÉN `'odoo_moodle_connector'` de los `depends` del fix.
Depends finales de `irg_admission_gender_fix`:
`['openeducat_admission', 'openeducat_core', 'isep_openeducat_sale']`.

No se tocó código: `models/res_partner.py` del propio fix ya define su propia
selección extendida de `gender` (`'m'/'f'/'o'/'male'/'female'/'not-sure'`) sin
importar ni depender de `odoo_moodle_connector` — es autocontenida, por lo que
quitar la dependencia del manifest no rompe esa lógica (mapeo de valores
legacy se mantiene intacto, tal como pidió el orquestador).

Verificación de carga real: se hizo `-u irg_admission_gender_fix,
isep_sale_order_admissions,isep_admission_from_student_field` sobre
`test_irg_db` (donde `odoo_moodle_connector` SÍ está instalado, por ser
dependencia transitiva de otros módulos ya instalados). Resultado: `Modules
loaded.` / `Registry loaded in 13.261s`, sin trazas de error de carga. El
warning `res.partner.gender: selection=[...] overrides existing selection;
use selection_add instead` ya existía ANTES de este cambio (mismo warning en
la ejecución previa con `odoo_moodle_connector` en depends); no es un efecto
nuevo de quitar la dependencia, es preexistente por cómo `res_partner.py`
redefine la selección con `fields.Selection([...])` en vez de
`selection_add`. Se documenta aquí tal como pidió el orquestador, sin
improvisar una solución no solicitada.

Verificado (L1-L3 del plan, con manifests ya corregidos): los 3 manifiestos
son dict Python válidos; el fix NO depende de
`isep_admission_from_student_field`; ambos módulos de admisión SÍ dependen
del fix.

## Tarea 7 — Tests nuevos test_gender_mapping.py

Archivo: `addons-extra/extrairg/irg_admission_gender_fix/tests/test_gender_mapping.py`

- Tag añadido a la clase: `@tagged('irg_gender', 'post_install', '-at_install')`
  (import `from odoo.tests import tagged`). Ejecutable de forma aislada con
  `--test-tags irg_gender`.
- `test_06_student_gender_over_order` (A2): se ejercita el helper
  `_irg_resolve_admission_gender` directamente sobre un `sale.order` (enfoque
  (a) del plan) en vez de montar el flujo completo de confirmación de venta,
  por ser más robusto en este entorno. Pedido con `gender='m'` (pagador) +
  partner estudiante con `gender='f'` → `order._irg_resolve_admission_gender(partner_f) == 'f'`
  (estudiante gana). Sin partner explícito, cae al `partner_id` del pedido
  (pagador, `'m'`).
- `test_07_explicit_other_not_overwritten` (A3): admisión creada con
  `gender='o'` explícito y partner "Laura Gomez" (adivinaría `'f'`, ver
  test_05) → se mantiene `'o'`. Repetido en `write`: fuerza a `'m'`, luego
  `write({'gender': 'o'})` → sigue `'o'`.
- `test_08_moodle_value_mapped_by_helper` (A4): partner con `gender='female'`
  (valor Moodle real en este entorno, definido en
  `odoo_moodle_connector/models/res_partner_custom.py`) → el helper resuelve
  a `'f'`; complementariamente, admisión creada con
  `gender=order._irg_resolve_admission_gender(partner) or 'o'` también queda
  en `'f'`.

**Desviación necesaria sobre `test_02` (preexistente):** el test original
`test_02_create_admission_from_partner_gender` creaba una admisión con
`'gender': 'o'` explícito y esperaba que el partner female (con género
correcto ya seteado) sobreescribiera a `'f'`. Esto CONTRADICE R3 (el fix ya
corregido en Tarea 5 respeta `'o'` explícito, no lo sobreescribe). Se quitó
el `'gender': 'o'` de ese create para que el test siga verificando el mapeo
desde el partner cuando no se informa género explícito (su intención
original), sin violar el nuevo comportamiento correcto.

**Desviación necesaria de fixtures (bug preexistente, no de género):** el
`setUp()` original fijaba `register.start_date/end_date` y
`batch.start_date/end_date` a fechas literales de junio 2026
(`'2026-06-01'`/`'2026-06-30'`). `op.admission.application_date` tiene
`default=fields.Datetime.now()`; al ejecutar la suite en fecha posterior a
esas fechas fijas (hoy 2026-07-03), la constraint
`_check_admission_register` (`openeducat_admission/models/admission.py`
línea 197) revienta con `ValidationError: Application Date should be between
Start Date & End Date...` en TODOS los tests que crean `op.admission` sin
pasar `application_date` explícito (afectaba a test_01, test_02, test_03,
test_05, test_07, test_08 — 6 de 8 tests). No es un defecto relacionado con
género; es un fixture con fechas fijas en el pasado respecto al reloj real
del sistema. Corregido haciendo el rango relativo a "hoy"
(`fields.Date.today() ± timedelta`) en vez de fechas literales, para que la
suite sea estable independientemente de cuándo se ejecute. Se usó
`fields.Date.today()` (no `fields.Date.context_today(self)`, que falló con
`AttributeError: 'TestGenderMapping' object has no attribute '_context'`
porque `self` en un `TransactionCase` no es un recordset).

Verificado (M1-M2 del plan): `test_06`/`test_07`/`test_08` existen, archivo
compila.

## Tarea 8 — Validación global (A1-A5)

Ejecutado en el contenedor `odoo16irg_local` contra `test_irg_db`:

**Paso 1 (A5)** — update de los 4 módulos:
```
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u isep_openeducat_sale,isep_sale_order_admissions,isep_admission_from_student_field,irg_admission_gender_fix \
  --stop-after-init --no-http
```
Resultado: `716 modules loaded in 24.87s` / `Modules loaded.` / `Registry
loaded in 28.262s`. Sin `circular`, sin `not met`, sin `Failed to
load/initialize`. A5 PASS.

**Paso 2 (A1-A4)** — suite de tests del módulo fix:
```
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_admission_gender_fix --test-enable --test-tags irg_gender \
  --stop-after-init --no-http
```
Resultado final (tras corregir fixtures de fecha y `context_today`):
`irg_admission_gender_fix: 10 tests 0.78s 1426 queries` /
`0 failed, 0 error(s) of 8 tests when loading database 'test_irg_db'`.
Los 8 métodos (`test_01`...`test_08`) se ejecutaron sin error
(`Starting TestGenderMapping.test_XX...` sin `ERROR:`/`FAIL:` subsiguiente
para ninguno). A1-A4 PASS.

## Notas de entorno para el Validator

- `docker exec ... python3 -m py_compile <ruta>` falla con
  `OSError: [Errno 30] Read-only file system: '.../__pycache__'` porque los
  addons están montados `:ro`. Esto NO es un error de sintaxis: usar
  `python3 -c "import py_compile; py_compile.compile('<ruta>', cfile='/tmp/x.pyc', doraise=True); print('OK')"`
  para evitar que intente escribir `__pycache__` junto al fuente, o
  simplemente `python3 -m py_compile <ruta>` en el HOST (fuera del
  contenedor) sobre el path del repo, que es equivalente en sintaxis Python.
- Logs completos de las ejecuciones guardados en el scratchpad de esta sesión
  (no en el repo): `irg_gender_update.log` / `irg_gender_update3.log` (Paso
  1) e `irg_gender_tests3.log` (Paso 2, versión final en verde). El Validator
  debe re-ejecutar los comandos para generar su propia evidencia.

## Cambios respecto al plan original (resumen)

1. Manifest del fix: se quitó también `odoo_moodle_connector` de `depends`
   (cambio de requisito R4b comunicado a mitad de misión), no solo
   `isep_admission_from_student_field` como decía el plan original.
2. `test_02` existente ajustado (quitado `'gender': 'o'` explícito) para no
   contradecir R3 tras el fix de Tarea 5.
3. Fixtures de fecha en `setUp()` cambiadas de literales fijos a relativos a
   `fields.Date.today()` — bug preexistente de robustez temporal, no
   relacionado con género, pero bloqueaba A1 si no se corregía.
4. `test_06`/`test_08` usan `fields.Date.today()` en vez de
   `context_today(self)` por incompatibilidad de `self` con `context_today`
   en `TransactionCase`.

## Tareas pendientes

Ninguna del plan (1-8) queda pendiente de implementación. Corresponde al
Validator ejecutar formalmente y emitir `03-validation.md`.

## Iteración 2 — MAYOR-1

Hallazgo del Reviewer (`02b-review.md`, MAYOR-1): octava ocurrencia del patrón
buggy sin corregir en `irg_admissions_by_student` (fuera del alcance
declarado del plan original, módulo desinstalado en `test_irg_db`).

Cambios aplicados en `addons-extra/extrairg/irg_admissions_by_student/`:

1. `models/sale_order.py:48` — sustituido
   `'gender': self.gender or target_partner.gender or 'o',`
   por `'gender': self._irg_resolve_admission_gender(target_partner) or 'o',`
   (mismo patrón usado en `isep_admission_from_student_field`: se pasa
   `target_partner`, no `self.partner_id`, porque este módulo también
   distingue alumno (`student_id`) de titular del pedido).
2. `__manifest__.py` — añadido `'irg_admission_gender_fix'` a `depends`.
   Depends finales: `['sale', 'isep_openeducat_sale',
   'irg_sale_order_extended', 'irg_admission_gender_fix']`.

Verificación de ausencia de ciclo: `irg_admission_gender_fix` depende de
`['openeducat_admission', 'openeducat_core', 'isep_openeducat_sale']`; ninguno
de esos módulos, ni ningún otro manifest del repo, depende de
`irg_admissions_by_student` (`grep -rl "irg_admissions_by_student" addons-extra
--include="__manifest__.py"` → sin resultados). Sin ciclo.

Verificación de código:
- `python3 -c "import ast; ast.literal_eval(...)"` sobre el manifest → OK,
  `depends` correctos.
- `python3 -m py_compile
  addons-extra/extrairg/irg_admissions_by_student/models/sale_order.py` →
  `COMPILE_OK`.
- `grep -n "_irg_resolve_admission_gender"
  addons-extra/extrairg/irg_admissions_by_student/models/sale_order.py` →
  línea 48 presente.

Verificación global (punto 3 del encargo): `grep -rnE "self\.gender or
.*\.gender or 'o'" addons-extra --include="*.py"` → sin coincidencias en todo
`addons-extra`. Ya no queda ninguna ocurrencia del patrón buggy.

No se ha instalado/actualizado el módulo en ningún contenedor (está
desinstalado en `test_irg_db`, tal como indica el encargo); solo se verificó
sintaxis y ausencia de ciclo por lectura estática. Pendiente para el Validator:
confirmar (si procede) que un `-u` de `irg_admissions_by_student` junto al
resto de módulos de la misión no introduce error de carga, si decide ampliar
el alcance de A5.

## Iteración 2b — Reversión de MAYOR-1 (orquestador)

Decisión del usuario: `irg_admissions_by_student` NO se usa en producción
(desinstalado también en local), así que no se toca. Revertidos con
`git checkout --` los dos cambios que la iteración 2 llegó a aplicar
(`models/sale_order.py` línea 48 y `__manifest__.py`). El hallazgo queda
documentado como deuda latente en la adenda de 02b-review.md. El Validator
NO debe esperar cambios en `irg_admissions_by_student`.
