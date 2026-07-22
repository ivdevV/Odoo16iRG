# iRG Gradebook Moodle Wizard

Sincronización puntual de notas desde Moodle a la libreta individual de un
alumno en Odoo 16. El addon añade un mapeo de asignaturas y actividades, lee
los `grade items` de Moodle y permite revisar o editar la nota antes de
aplicarla a `app.gradebook.result`.

## Dependencias e instalación

- `isep_gradebook`
- `irg_moodle_grades_sync`
- Credenciales válidas en Odoo Moodle Connector para usar el servicio real.

El módulo técnico es `irg_gradebook_moodle_wizard` y su versión inicial es
`16.0.1.0.0`. Se instala o actualiza mediante el flujo Odoo habitual del
proyecto. En desarrollo y validación debe usarse `docker-compose.local.yml`;
si se trabaja desde un worktree, debe añadirse un overlay que monte ese
checkout en `/mnt/extra-addons`.

## Configuración del mapeo

El menú **Mapeo Moodle libreta** permite relacionar:

- una `op.subject` de Odoo;
- un curso Moodle; y
- una o más actividades Moodle, cada una tipada como `quiz` o `assign`.

Solo el administrador de sistema puede crear, modificar o eliminar mapas. Los
usuarios internos pueden leerlos. No se modifica `irg.moodle.subject.map` ni
el cron de `irg_moodle_grades_sync`.

Cada pareja asignatura–curso Moodle admite un único mapa; si una asignatura
tiene varios mapas activos, el wizard la marca como incompatible. Los IDs de
curso y actividad deben ser enteros positivos dentro del rango de PostgreSQL
`1..2147483647`; una actividad no puede repetirse dentro del mismo mapa.

## Uso del wizard

1. Abra una libreta individual en proceso.
2. Pulse **Sincronizar con Moodle**.
3. Revise el emparejamiento, estados, actividades y notas encontradas.
4. Edite **Nota a aplicar** si procede y desmarque las líneas que no quiera
   aplicar.
5. Pulse **Aplicar notas**.

El acceso está limitado a Faculty y Gradebook Admin. La misma autorización se
comprueba en servidor; ocultar el botón no sustituye el control de permisos.
Una libreta finalizada no puede abrir ni aplicar la sincronización.

El alumno se busca por este orden:

1. `res.partner.md_id`;
2. email normalizado; y
3. nombre normalizado, únicamente si la coincidencia es única.

Los posibles estados de una línea son **Encontrada**, **Sin mapeo**, **Sin
nota en Moodle**, **Alumno no encontrado** e **Incompatible**. Solo una línea
**Encontrada** puede aplicarse.

## Regla de agregación y compatibilidad

La decisión funcional elegida para esta versión conserva una sola línea
agregada por asignatura y tipo:

- `quiz` se escribe como `survey_type='exam'`;
- `assign` se escribe como `survey_type='assignment'`; y
- las actividades calificadas del mismo tipo se convierten a la escala de la
  libreta y se promedian.

Cada actividad se transforma con
`graderaw / grademax * grading_scale`. Valores no finitos, máximos nulos o no
positivos y notas fuera de escala se rechazan o quedan sin nota.

El wizard no modifica los computes base de `isep_gradebook`. Para evitar que
una única media sustituya una estructura que espera varias notas, una línea se
marca **Incompatible** cuando:

- la cantidad efectiva del template para ese tipo no es exactamente `1`;
- ya existe una línea manual del mismo tipo;
- hay varios mapas activos, IDs `id`/`cmid` ambiguos o un `itemmodule` que no
  coincide con el tipo mapeado; o
- existen duplicados Moodle heredados que impiden un upsert inequívoco.

Las notas creadas por el addon llevan `is_moodle=True`. La clave almacenada
`moodle_sync_key` garantiza una única nota Moodle por asignatura y tipo. Una
resincronización actualiza esa misma fila y no duplica el resultado. El flujo
usa locks ordenados y revalida permisos, pertenencia, estado, escala y
compatibilidad al aplicar.

## Importación desde `MAP_ASIGNATURAS`

El script `tools/import_map_csv.py` importa un CSV UTF-8 con estas columnas:

- `Moodle Course ID`
- `Odoo Subject ID`
- `Odoo Subject Name`
- `Curso Nombre`
- `Moodle IDs List`
- `Moodle Names Found`

Ejemplo desde `odoo shell`:

```python
exec(open(
    "/mnt/extra-addons/extrairg/irg_gradebook_moodle_wizard/"
    "tools/import_map_csv.py"
).read())
run_import(env, "/tmp/map_asignaturas.csv")
env.cr.commit()
```

El import es idempotente por asignatura y curso. Al actualizar un mapa,
regenera todas sus actividades. Una fila inválida se omite de forma atómica y
no borra el mapa existente. Los IDs de asignatura del Excel pertenecen a la
base de origen: deben validarse antes de ejecutar el import en otra base. El
CSV actual de `MAP_ASIGNATURAS` contiene únicamente quizzes; `assign` está
soportado por el modelo y el wizard, pero no se importa desde esa hoja.

## Pruebas y validación

La validación independiente del commit funcional
`a0757b59a69710d8f2427d580beeb676566001b4` ejecutó:

```bash
docker compose -f docker-compose.local.yml \
  -f missions/irg-gradebook-moodle-wizard/docker-compose.worktree.yml \
  run --rm --no-deps odoo_local \
  odoo -c /etc/odoo/odoo.conf -d test_irg_db \
  -u irg_gradebook_moodle_wizard --test-enable --stop-after-init \
  --log-level=test
```

Resultado: 44 métodos, 50 tests/subtests en las estadísticas de Odoo, 0
fallos y 0 errores. La suite cubre servicio y esquema Moodle, matching,
conversión, tipos, incompatibilidades, ACL, upsert, constraints, concurrencia,
retry e importación CSV.

El smoke UI end-to-end pasó contra un Moodle local simulado: botón, modal,
nota editable, aplicación, actualización de promedios y segunda sincronización
sin duplicados. El smoke contra un WS Moodle real quedó omitido porque ninguna
de las 101 bases locales inspeccionadas contiene credenciales. Por ello, la
semántica real de los IDs del Excel (`id` frente a `cmid`) no se pudo confirmar
localmente; el código acepta ambos espacios de IDs y rechaza colisiones.

Consulte el [plan aprobado](../../../docs/superpowers/plans/2026-07-21-irg-gradebook-moodle-wizard.md)
y la [verificación de la misión](../../../missions/irg-gradebook-moodle-wizard/verification.json)
para el alcance y la evidencia completa.

## Limitaciones

- El flujo es individual; no sincroniza cursos ni batches completos.
- No importa el mapeo HomeClass.
- No ejecuta migraciones ni un import automático en producción.
- Requiere credenciales Moodle y mapas consistentes antes de abrir el wizard.
- No mezcla una nota Moodle agregada con líneas manuales del mismo tipo ni con
  templates cuya cantidad sea distinta de uno.
