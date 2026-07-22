# Re-review independiente — routing curso/asignatura Moodle

## Veredictos finales

- **Spec compliance: PASS**
- **Code quality: APPROVED**
- **Readiness: READY_FOR_INDEPENDENT_VALIDATION**

Los tres findings bloqueantes de la Review inicial están cerrados. No se
detectaron regresiones funcionales nuevas ni observaciones Critical/Important.
La aprobación habilita la fase de Validación independiente; no equivale al
cierre de misión ni autoriza commit, push o PR.

## Cierre de findings previos

### Critical — coherencia padre/curso Moodle: CLOSED

- `addons-extra/extrairg/irg_gradebook_moodle_routing/models/moodle_routing.py:62`
- `addons-extra/extrairg/irg_gradebook_moodle_routing/models/moodle_routing.py:81`
- `addons-extra/extrairg/irg_gradebook_moodle_routing/wizard/moodle_sync_wizard.py:73`

El hijo valida por ORM que su `moodle_course_id` coincide con el padre y que la
asignatura pertenece al curso Odoo del padre. El padre vuelve a validar sus
hijos al editar `op_course_id` o `moodle_course_id`, evitando corromperlos desde
el otro extremo. Además, antes de delegar al método heredado y antes de
`_get_service`, el wizard inspecciona todos los mapas activos del padre
seleccionado y bloquea cualquier histórico incoherente. Así, incluso una fila
corrupta introducida fuera del ORM no puede dirigir la consulta a otro curso
Moodle.

La cobertura añadida prueba creación incoherente, cambio de ID/curso en el
padre y corrupción directa en SQL con `_get_service` no llamado.

### Important — borrado y pérdida de líneas: CLOSED

- `addons-extra/extrairg/irg_gradebook_moodle_routing/tools/import_moodle_routing_csv.py:197`
- `addons-extra/extrairg/irg_gradebook_moodle_routing/tests/test_moodle_routing.py:392`

El importador ya no limpia el `One2many` ni ejecuta `unlink`. Hace upsert por
Activity ID: conserva IDs de registro, líneas ausentes del CSV, tipos existentes
y nombres existentes cuando la fuente no aporta nombre; solo crea los IDs
nuevos y actualiza nombres no vacíos. Esto cubre también las cinco filas
HomeClass reales con menos nombres que Activity IDs sin destruir metadatos
previos. El scan dirigido no encontró operaciones destructivas en el
importador.

### Important — descartes silenciosos y headers: CLOSED

- `addons-extra/extrairg/irg_gradebook_moodle_routing/tools/import_moodle_routing_csv.py:43`
- `addons-extra/extrairg/irg_gradebook_moodle_routing/tools/import_moodle_routing_csv.py:56`

Los tres CSV validan ahora sus encabezados obligatorios y fallan de forma
explícita si falta alguno. `summary.sources` registra por fuente filas leídas,
aceptadas, descartadas y motivos agregados, sin exponer datos de filas.

La comprobación de solo lectura con los ficheros reales confirmó:

- HomeClass: 21 leídas, 15 aceptadas, 6 descartadas como `invalid_values` y 15
  parejas autorizadas.
- Online: 253 leídas, 253 aceptadas, 0 descartadas y 15 IDs distintos.
- Asignaturas: headers válidos y 410 filas legibles.

Por tanto las seis filas HomeClass que antes desaparecían quedan ahora
representadas en el resumen estructurado.

## Findings de esta re-review

### Critical

Ninguno.

### Important

Ninguno.

### Minor

1. **El test de mutaciones del padre encadena dos `ValidationError` sin
   savepoints independientes.**

   - Archivo:
     `addons-extra/extrairg/irg_gradebook_moodle_routing/tests/test_moodle_routing.py:193`

   Después del primer `write` rechazado, el test captura la excepción sin
   restaurar explícitamente el estado antes de probar el cambio de
   `op_course_id`; la segunda aserción podría quedar satisfecha por la primera
   incoherencia. El código inspeccionado sí valida ambas ramas, por lo que no es
   bloqueante, pero conviene usar un `savepoint` por escritura o fixtures padre
   separados para que cada regresión demuestre una causa única.

## Ausencia de regresiones funcionales

- Se mantiene la selección estricta HC/online/año y el fallback genérico.
- El guard server-side continúa ejecutándose antes del routing y el heredado
  continúa ejecutándose después con el contexto parental.
- El filtro `_search` sigue limitado a la presencia de la clave contextual y
  no cambia búsquedas base sin routing.
- No se ampliaron ACL ni permisos del wizard.
- No se modificaron addons existentes; el cambio funcional permanece dentro
  del addon puente nuevo.
- La importación sigue siendo estricta con IDs PostgreSQL positivos,
  autorizaciones y pertenencia asignatura/curso, sin desactivar históricos.

## Evidencia revisada

- RED de corrección: exit 1, 16 métodos / 18 tests-subtests, 7 fallos y 1 error
  que reproducen los findings; microciclo parental adicional en RED.
- GREEN de corrección: exit 0, 17 métodos / 19 tests-subtests, 0 fallos y 0
  errores.
- Checks declarados: compileall/manifest/XML/ACL, `git diff --check`, scan de
  borrado destructivo, overlay y restauración, todos `pass`.
- Re-review: inspección completa de modelos, wizard e importador corregidos;
  revisión focalizada de los tests nuevos y ejecución de diagnóstico de solo
  lectura sobre headers/estadísticas de los CSV reales.
- Conforme a la instrucción de Review, no se repitió la suite Odoo del
  codificador ni se ejecutó `run_import` contra una base.

## Gate

**APPROVED para Validación independiente.** El finding Minor es no bloqueante
y puede corregirse sin cambiar el comportamiento funcional; si se modifica
solo ese test, no requiere reabrir esta Review de código.

## Nota final tras ajuste de formato detectado en Validación

Se revisó de forma acotada la eliminación de la línea física vacía adicional
al EOF en:

- `addons-extra/extrairg/irg_gradebook_moodle_routing/__init__.py`;
- `addons-extra/extrairg/irg_gradebook_moodle_routing/models/__init__.py`;
- `addons-extra/extrairg/irg_gradebook_moodle_routing/tests/__init__.py`;
- `addons-extra/extrairg/irg_gradebook_moodle_routing/wizard/__init__.py`.

La lectura por líneas y bytes confirma que permanecen exactamente los mismos
imports (`models`, `wizard`, `moodle_routing`, `test_moodle_routing` y
`moodle_sync_wizard`) y que cada archivo conserva un único salto de línea POSIX
tras su última sentencia. No cambió ningún import, símbolo descubierto, orden
de carga ni comportamiento de runtime.

No se repitió la suite por tratarse exclusivamente de formato sin cambio
funcional. El estado de esta Review se mantiene sin cambios:
**Spec compliance: PASS**, **Code quality: APPROVED** y
**Readiness: READY_FOR_INDEPENDENT_VALIDATION**.

## Nueva ronda tras Final Review funcional

### Veredictos

- **Spec compliance: PASS**
- **Code quality: APPROVED**
- **Readiness: READY_FOR_INDEPENDENT_VALIDATION**

Se revisaron de nuevo `final-review.md`, el modelo, el wizard, el importador,
los tests modificados y las evidencias `final-review-fix-red.txt` /
`final-review-fix-green.txt`. El finding Important del Final Review y el Minor
parental previo están cerrados, sin findings Critical, Important ni Minor
abiertos en esta ronda funcional.

### Parser Online exacto: CLOSED

- `addons-extra/extrairg/irg_gradebook_moodle_routing/models/moodle_routing.py:8`
- `addons-extra/extrairg/irg_gradebook_moodle_routing/models/moodle_routing.py:13`

`parse_moodle_course_name()` es ahora la única fuente de clasificación para el
modelo y el importador. Cuando aparece el token autoritativo `(ONLINE`, exige
exactamente una coincidencia case-insensitive de `(ONLINE)` o
`(ONLINE AAAA)`, con `AAAA` formado por cuatro dígitos. Si no hay coincidencia,
hay más de una o queda otro token `(ONLINE` sin consumir, devuelve modalidad y
edición falsas. La ausencia del token literal continúa siendo HomeClass, tal
como exige el contrato original para cualquier otro nombre no vacío.

La inspección y el diagnóstico puro del parser confirmaron:

- `(ONLINE)` → online genérico;
- `(ONLINE 2026)` y su variante de mayúsculas/minúsculas → online con edición;
- `(ONLINE2026)`, `(online 26)` y `(OnLiNe 2026 EXTRA)` → no seleccionables.

### Importación de marcadores malformados: CLOSED

- `addons-extra/extrairg/irg_gradebook_moodle_routing/tools/import_moodle_routing_csv.py:155`
- `addons-extra/extrairg/irg_gradebook_moodle_routing/tests/test_moodle_routing.py:556`

El importador invoca el mismo parser antes de comprobar inventarios o tocar el
ORM. Un marcador Online malformado incrementa `skipped`,
`skipped_by_reason.invalid_online_marker` y las estadísticas descartadas de la
fuente de asignaturas; no crea ni actualiza mapas. El test cubre los tres casos
reproducidos y verifica ausencia de registros Moodle 51/52/53.

### Bloqueo pre-servicio: CLOSED

- `addons-extra/extrairg/irg_gradebook_moodle_routing/wizard/moodle_sync_wizard.py:25`
- `addons-extra/extrairg/irg_gradebook_moodle_routing/tests/test_moodle_routing.py:289`

Los mapas malformados almacenan `modality=False`, por lo que nunca entran en el
dominio HC/online. Si son el único supuesto candidato ONL, la resolución exige
un fallback genérico único y lanza `UserError` antes de construir el wizard
enrutado y antes de `_get_service`. La regresión comprueba expresamente que el
servicio no se llama.

### Aislamiento del test parental: CLOSED

- `addons-extra/extrairg/irg_gradebook_moodle_routing/tests/test_moodle_routing.py:205`

Las dos mutaciones negativas usan ahora padres e hijos distintos:
`moodle_parent` prueba el cambio de ID Moodle y `course_parent` prueba el cambio
de curso Odoo. La primera excepción ya no puede satisfacer la segunda rama por
estado residual. La evidencia RED declara además que esta regresión aislada ya
pasaba antes de implementar el parser.

### Evidencia y gate

- RED: exit 1, 20 métodos / 22 tests-subtests, 5 fallos esperados y 0 errores.
- GREEN: exit 0, 20 métodos / 22 tests-subtests, 0 fallos y 0 errores.
- Checks declarados: Python/manifest/XML/ACL, whitespace/diff, ausencia de
  reset destructivo, overlay/restauración y Git index vacío, todos `pass`.
- No se repitió la suite Odoo ni se ejecutó importación ORM durante esta
  Review; el único diagnóstico ejecutado aisló la función pura del parser.
- No se editó código funcional ni se realizó stage, commit, push o PR.

**APPROVED para una nueva Validación independiente de esta versión
funcional.**
