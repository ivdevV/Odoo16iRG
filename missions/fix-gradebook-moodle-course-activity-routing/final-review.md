# Re-review final integral — routing curso/asignatura Moodle

## Alcance

Revisión final de la versión corregida del addon
`irg_gradebook_moodle_routing`, los artefactos de la misión
`fix-gradebook-moodle-course-activity-routing` y la entrada de knowledge
asociada, sobre la base
`8656ad1f4182f5ca23a51ced75282c012e960f02`.

Se inspeccionaron de nuevo modelo, wizard, importador, tests, Review de código,
`verification.json`, README, changelog, ejecución y knowledge. Conforme al
encargo, no se repitieron pruebas ni se modificó código funcional.

## Cierre de los findings anteriores

### Important — marcador Online malformado: CLOSED

- `addons-extra/extrairg/irg_gradebook_moodle_routing/models/moodle_routing.py:8`
- `addons-extra/extrairg/irg_gradebook_moodle_routing/models/moodle_routing.py:13`
- `addons-extra/extrairg/irg_gradebook_moodle_routing/tools/import_moodle_routing_csv.py:155`
- `addons-extra/extrairg/irg_gradebook_moodle_routing/tests/test_moodle_routing.py:149`
- `addons-extra/extrairg/irg_gradebook_moodle_routing/tests/test_moodle_routing.py:289`
- `addons-extra/extrairg/irg_gradebook_moodle_routing/tests/test_moodle_routing.py:556`

El modelo y el importador comparten ahora `parse_moodle_course_name()`. Solo una
coincidencia case-insensitive exacta de `(ONLINE)` o `(ONLINE AAAA)` produce un
mapa Online; un token malformado, repetido o no consumido devuelve modalidad
falsa. El importador lo contabiliza como `invalid_online_marker` antes de tocar
el ORM, y el wizard no puede seleccionarlo ni contactar Moodle. Las regresiones
cubren clasificación, importación sin mapas y bloqueo pre-servicio.

### Minor — aislamiento del test parental: CLOSED

- `addons-extra/extrairg/irg_gradebook_moodle_routing/tests/test_moodle_routing.py:205`

Las mutaciones de Moodle Course ID y curso Odoo usan ahora dos padres e hijos
distintos, por lo que el estado residual de la primera excepción no puede hacer
pasar la segunda rama.

### Minor — changelog funcional incompleto: CLOSED

- `missions/fix-gradebook-moodle-course-activity-routing/CHANGELOG.md:5`

La entrada de versión enumera ya el modelo padre, routing, filtro de asignaturas,
constraints, ACL, vistas, importador, conservación histórica y endurecimiento de
marcadores Online.

### Minor — cronología de validación: CLOSED

- `missions/fix-gradebook-moodle-course-activity-routing/execution.md:65`

La validación fallida por whitespace precede ahora a su corrección, Re-review y
revalidación. Las rondas posteriores de fix funcional, Review, defecto docutils,
corrección documental y revalidación final también están ordenadas.

### Minor — estado de validación desfasado en README y knowledge: CLOSED

- `addons-extra/extrairg/irg_gradebook_moodle_routing/README.md:162`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_gradebook_moodle_course_activity_routing.md:54`
- `missions/fix-gradebook-moodle-course-activity-routing/verification.json:2`

Ambos documentos reflejan ya `verification.json: passed`, el upgrade limpio sin
errores ni warnings de docutils, los 20 métodos / 22 tests-subtests aprobados y
el límite transparente del smoke real por ausencia de registros Odoo fuente.

## Findings finales

### Critical

Ninguno.

### Important

Ninguno.

### Minor

Ninguno.

## Coherencia funcional y gates

La versión funcional cumple el objetivo: el lote resuelve primero el mapa de
curso HC/ONL; Online prioriza el año y usa solo un fallback genérico inequívoco;
los mapas de asignatura y Activity IDs quedan limitados al padre seleccionado;
HomeClass se autoriza por su CSV, Online por inventario y nombre válido, y Odoo
`1` / Moodle `36` permanece excluido mientras no esté autorizado. Se conservan
la integridad padre/hijo, las ACL de mínimo privilegio, el guard server-side y el
upsert no destructivo.

La Review funcional nueva está aprobada y `verification.json` declara `passed`
con 20 métodos / 22 pruebas y subpruebas, import real reversible, smoke de
marcadores malformados, checks estáticos y cleanup. Esta Re-review no repitió
ninguno de esos checks.

La comprobación temporal acotada desde la Re-review anterior muestra que solo
`README.md` y la entrada de knowledge cambiaron; ninguno de los 12 archivos
funcionales del addon fue modificado. El estado Git sigue sin stage, commit,
push ni PR.

## Gate

**Ready to deliver: Yes.** No quedan findings Critical, Important ni Minor
abiertos. Los gates funcionales y documentales son coherentes y están cerrados;
cualquier commit, push o PR sigue requiriendo autorización explícita separada.
