# Administración e importación jerárquica del mapeo Moodle — Diseño

**Fecha:** 2026-07-22
**Estado:** diseño aprobado; plan de implementación redactado
**Alcance:** administración de mapas curso/asignatura/actividad y carga desde interfaz y `odoo shell`

## Objetivo

Corregir la administración del mapeo de Moodle para representar explícitamente
dos relaciones distintas:

```text
curso Odoo
  -> uno o varios cursos Moodle
       -> asignaturas Odoo de ese curso
            -> uno o varios Activity IDs Moodle
```

La solución debe importar los dos CSV consolidados entregados por el usuario,
mostrar todo el contexto Odoo/Moodle en las tablas y ofrecer la misma lógica de
importación tanto desde un wizard como desde `odoo shell`.

## Decisiones cerradas

- Se mantiene el modelo normalizado y jerárquico; no se guardan listas de IDs
  en campos de texto como fuente de verdad.
- Un curso Odoo puede tener varios Moodle Course IDs, por ejemplo HomeClass,
  Online genérico y Online de una edición concreta.
- Una asignatura dentro de un curso Moodle puede tener varios Activity IDs.
- Se usarán exactamente dos fuentes funcionales:
  `mapeo cursos.csv` y `Mapeo asignaturas.csv`.
- Las filas de asignaturas sin Activity IDs no crean mapas de asignatura. Se
  contabilizan como omitidas; esto cubre TFM, Prácticas y cualquier otro caso
  sin actividades, sin depender del nombre de la asignatura.
- Los Activity IDs repetidos dentro de una fila se deduplican conservando el
  orden de la primera aparición y se notifican como advertencia.
- El wizard y el shell consumen el mismo servicio interno de análisis y
  aplicación.
- La importación es idempotente y conservadora: hace upsert, añade actividades
  nuevas y actualiza metadatos no vacíos, pero no borra, desactiva ni vacía
  mapas históricos.
- La selección de curso Moodle por código de lote (`HC`/`ONL`) y año Online
  continúa siendo responsabilidad de `irg_gradebook_moodle_routing`.

## Encaje en la arquitectura existente

Se creará el addon puente nuevo
`irg_gradebook_moodle_mapping_admin`, en `addons-extra/extrairg/`. Dependerá de
`irg_gradebook_moodle_routing` y extenderá sus modelos y vistas mediante
`_inherit` y vistas heredadas. No se modificará directamente ningún addon
existente.

La solución reutilizará estas entidades ya implantadas:

- `irg.gradebook.moodle.course.map`: pareja curso Odoo / curso Moodle, nombre,
  modalidad y edición.
- `irg.gradebook.moodle.map`: pareja asignatura Odoo / curso Moodle vinculada
  al mapa de curso padre mediante `course_map_id`.
- `irg.gradebook.moodle.map.line`: Activity ID y metadatos de la actividad.

El addon nuevo añadirá únicamente las relaciones inversas, campos auxiliares
de presentación, servicio de importación, wizard, vistas, permisos y pruebas
necesarios. Los mapas históricos sin padre se conservarán, pero seguirán fuera
del routing estricto.

## Modelo visible y navegación

### Cursos Moodle

El listado de cursos mostrará una fila por pareja curso Odoo / curso Moodle:

- curso Odoo y su ID de base de datos;
- Moodle Course ID y nombre Moodle;
- modalidad calculada (`HomeClass` u `Online`);
- edición Online, si existe;
- número de asignaturas mapeadas;
- estado activo.

El formulario incluirá una pestaña de asignaturas vinculadas. Así, un mismo
curso Odoo podrá aparecer en varias filas, una por cada Moodle Course ID, y
cada fila contendrá únicamente las asignaturas de esa edición Moodle.

### Asignaturas Moodle

El listado plano de asignaturas mostrará:

- curso Odoo y su ID;
- mapa de curso Moodle, Moodle Course ID y nombre Moodle;
- asignatura Odoo, su ID, nombre y código;
- cantidad de Activity IDs y un resumen legible de ellos;
- estado activo.

El formulario permitirá administrar las líneas de actividad como registros
individuales. No se expondrá un campo de texto editable con IDs separados por
comas. La integridad existente seguirá exigiendo que la asignatura pertenezca
al curso Odoo padre y que padre e hijo usen el mismo Moodle Course ID.

## Contrato de los CSV

Los dos ficheros usarán separador `;`. El lector admitirá UTF-8 con BOM y, como
compatibilidad con los ficheros entregados, MacRoman.

### `mapeo cursos.csv`

Encabezados entregados:

- `Moodle Course ID`
- `Odoo Subject Name`
- `Odoo Subject ID`
- `Nombre del Curso`

En este fichero concreto, `Odoo Subject Name` y `Odoo Subject ID` significan
respectivamente **nombre e ID del curso Odoo**. El importador aceptará también
los alias futuros `Odoo Course Name` y `Odoo Course ID`. Si una fuente contiene
simultáneamente el encabezado legado y el canónico con valores distintos, la
fila se rechazará como ambigua.

Cada fila debe contener IDs enteros positivos, un curso Odoo existente, un
nombre Odoo coherente tras recortar espacios, compactar espacios internos y
comparar sin distinguir mayúsculas, y un nombre Moodle válido. La modalidad y
edición se derivan de `Nombre del Curso` usando las reglas estrictas ya
implantadas: solo `(ONLINE)` y `(ONLINE AAAA)` representan Online; un nombre
sin marcador Online representa HomeClass; un marcador Online malformado se
rechaza.

Este CSV sustituye a los inventarios separados HomeClass/Online como fuente
autorizadora. Puede contener varias filas con el mismo curso Odoo y distintos
Moodle Course IDs.

### `Mapeo asignaturas.csv`

Encabezados obligatorios:

- `Curso Nombre`
- `Odoo Course ID`
- `Moodle Course ID`
- `Odoo Subject Name`
- `Odoo Subject ID`
- `Odoo Subject Code`
- `Moodle IDs List`
- `Moodle Names Found`

`Reasoning`, `Match Type` y `Processed Date` se aceptan como metadatos de la
fuente, pero no son necesarios para el routing ni se persisten.

Cada fila con actividades debe cumplir todo lo siguiente:

1. La pareja `Odoo Course ID` / `Moodle Course ID` existe en el CSV de cursos
   de la misma carga.
2. El curso y la asignatura existen en Odoo.
3. La asignatura pertenece al curso Odoo.
4. Nombre y código de asignatura coinciden con Odoo tras normalización de
   espacios y comparación sin distinguir mayúsculas.
5. `Curso Nombre` coincide con el nombre Moodle de la pareja de curso.
6. `Moodle IDs List` contiene enteros positivos separados por comas.

Los nombres de `Moodle Names Found` se alinean posicionalmente con los IDs
usando `|`. Para un ID repetido se conserva la primera aparición; si su primer
nombre está vacío y una repetición posterior aporta nombre, se conserva el
primer nombre no vacío. Los nombres adicionales o ausentes generan advertencia
pero no invalidan IDs válidos.

Si varias filas describen la misma pareja curso Moodle / asignatura Odoo, sus
Activity IDs se unen de forma estable. El tipo de una línea existente se
conserva; las líneas nuevas usan `quiz`, igual que el importador actual, porque
los CSV no aportan un tipo autoritativo.

Si esas filas repetidas declaran padres Odoo distintos para la misma clave de
asignatura/curso Moodle, no se mezclan: la fila conflictiva se omite como
`conflicting_subject_parent` para impedir contaminación entre cursos.

## Servicio de importación compartido

El servicio tendrá dos fases explícitas:

1. **Analizar:** leer bytes, validar encabezados y filas y construir un plan de
   importación sin escribir mapas persistentes.
2. **Aplicar:** recibir un plan validado, volver a comprobar las referencias
   Odoo relevantes y ejecutar los upserts dentro de la transacción actual.

El plan conservará también el nombre del curso Odoo y el nombre/código de la
asignatura Odoo recibidos en los CSV. La aplicación comparará esos valores
normalizados con el estado actual justo antes de escribir; un cambio
concurrente bloqueará toda la transacción.

El plan contendrá las operaciones normalizadas y un resumen con:

- filas leídas, válidas, omitidas y advertidas por fichero;
- mapas de curso a crear o actualizar;
- mapas de asignatura a crear o actualizar;
- actividades a crear o cuyos nombres se actualizarán;
- conteos por motivo de omisión o advertencia.

Errores de fichero como encabezados ausentes, codificación ilegible o CSV no
parseable bloquean el análisis completo. Errores de una fila concreta la
omiten y permiten previsualizar e importar las filas válidas. Un error ORM
inesperado durante la aplicación revierte toda la confirmación; nunca queda una
aplicación parcial dentro de esa transacción.

Las claves de upsert serán las ya establecidas:

- curso: `(op_course_id, moodle_course_id)`;
- asignatura: `(op_subject_id, moodle_course_id)` y su `course_map_id` íntegro;
- actividad: `(map_id, moodle_activity_id)`.

Antes de la primera escritura, la aplicación validará el plan completo,
incluidos tipos, claves únicas, padres coherentes, actividades no vacías e IDs
de actividad únicos. Esto también protege planes construidos manualmente desde
shell. La aplicación no ejecutará `unlink`, no sustituirá el One2many completo
y no hará `commit`. El propietario de la transacción —la petición Odoo o el
administrador en shell— decide el commit.

## Wizard de interfaz

Solo los administradores de sistema podrán abrirlo o ejecutar sus acciones. El
control se aplicará tanto en ACL/grupos de la vista como dentro de los métodos
server-side.

El wizard `Importar mapeo Moodle` tendrá:

- campo binario obligatorio `mapeo cursos.csv`;
- campo binario obligatorio `Mapeo asignaturas.csv`;
- estado `Borrador`, `Validado` o `Aplicado`;
- resumen de validación legible y conteos por motivo;
- botones `Validar`, `Confirmar importación` y `Cancelar`.

`Validar` solo analizará los archivos. `Confirmar importación` volverá a
analizar los mismos bytes en servidor y aplicará ese resultado, evitando
confiar en un resumen o plan manipulable desde el cliente. Si los archivos
cambian, el wizard vuelve a estado borrador y exige otra validación. Tras la
aplicación mostrará el resumen final y acciones para abrir los listados de
mapas de curso y asignatura filtrados por los registros afectados.

Los nombres de archivo son informativos; la interfaz nunca recibirá ni abrirá
rutas arbitrarias del servidor.

## Uso desde `odoo shell`

El wrapper técnico aceptará dos rutas absolutas controladas por el
administrador y ofrecerá las mismas dos fases. El uso previsto será equivalente
a:

```python
from odoo.addons.irg_gradebook_moodle_mapping_admin.tools import import_mapping

plan = import_mapping.analyze_paths(
    env,
    "/ruta/controlada/mapeo cursos.csv",
    "/ruta/controlada/Mapeo asignaturas.csv",
)
print(plan.summary)

result = import_mapping.apply_plan(env, plan)
print(result)
env.cr.commit()  # solo tras revisar y decidir persistir
```

Para una comprobación sin cambios basta con ejecutar `analyze_paths`; no se
necesita un rollback porque esta fase no escribe mapas persistentes.

## Seguridad e integridad

- La misión es `full` y de capacidad `complex`: supera cinco archivos, cambia
  administración de datos y cruza modelos, importador, wizard y vistas.
- Antes de implementar, el Security Advisor revisará permisos, validación de
  binarios, transacciones, conservación histórica y ausencia de rutas web.
- No se usará `sudo()` para saltar permisos. El usuario ejecutor deberá tener
  derechos administrativos reales sobre los modelos.
- El contenido CSV decodificado tendrá un máximo de 10 MiB. Para el wizard se
  comprobará primero el tamaño base64 codificado máximo
  `4 * ceil(10 MiB / 3)`, antes de invocar al decodificador, y se repetirá el
  límite sobre los bytes obtenidos. `create` y `write` del transient aplicarán
  el límite codificado antes de persistir el campo, incluso por RPC directo.
- El adaptador de shell solo aceptará rutas absolutas y leerá como máximo
  10 MiB + 1 byte, sin confiar en una secuencia vulnerable `stat/read`.
- Los IDs deben estar entre 1 y 2.147.483.647.
- Los mensajes y resúmenes no registrarán el contenido completo de las filas
  ni datos personales; solo número de fila, clave técnica y motivo.
- Los constraints actuales de coherencia padre/hijo continúan siendo la última
  barrera server-side.

## Tratamiento de los datos entregados

La carga consolidada será autoritativa respecto a qué parejas curso Odoo /
curso Moodle pueden importarse en esa ejecución. Por tanto, las filas de
asignaturas para parejas ausentes en `mapeo cursos.csv`, incluidas actualmente
las parejas Odoo/Moodle `(8, 24)` y `(8, 47)`, se mostrarán como omitidas por
`missing_course_pair` hasta que se añadan al CSV de cursos.

Las filas vacías finales se contabilizarán como `blank_row` y no crearán
registros. Las filas sin Activity IDs se contabilizarán como `no_activity_ids`.
Los duplicados se contabilizarán como `duplicate_activity_id` sin descartar los
IDs únicos de la fila.

## Pruebas y criterios de aceptación

La implementación seguirá TDD y añadirá pruebas Odoo para:

1. Parseo UTF-8 BOM y MacRoman con `;`.
2. Encabezados legados y canónicos del CSV de cursos, incluido conflicto entre
   alias.
3. Un curso Odoo con varios Moodle Course IDs HomeClass/Online.
4. Una asignatura con varios Activity IDs.
5. Omisión de cualquier fila sin actividades sin crear un mapa vacío.
6. Deduplicación estable de IDs y alineación de nombres.
7. Rechazo por curso/asignatura inexistente, pertenencia incorrecta, nombres o
   código incoherentes y pareja de curso ausente.
8. Unión estable de filas repetidas para la misma asignatura y curso Moodle.
9. Idempotencia y conservación de líneas, tipos, históricos y metadatos no
   vacíos.
10. Ausencia de escrituras persistentes durante el análisis.
11. Atomicidad de la aplicación ante un fallo ORM.
12. Equivalencia entre la entrada binaria del wizard y las rutas del shell.
13. Restricción real del wizard a administradores, incluida llamada directa a
    métodos server-side por un usuario interno sin privilegios.
14. Vistas instalables con todas las columnas de curso, asignatura y actividad.
15. Regresión del routing `HC`/`ONL`, selección por año y aislamiento por mapa
    padre.

Las pruebas del upload cubrirán exactamente 10 MiB, un byte decodificado por
encima, base64 inválido, base64 codificado por encima del máximo y escritura
RPC directa excesiva. La prueba del tamaño codificado parcheará
`base64.b64decode` para demostrar que el rechazo ocurre antes de decodificar.
Todos los métodos públicos del wizard comprobarán administrador, singleton y
estado server-side; confirmar exigirá estado `validated`.

La validación se ejecutará mediante `docker-compose.local.yml` sobre una base
de prueba, con upgrade del addon, suite Odoo, compilación Python, parseo XML,
revisión de ACL y un smoke reversible con copias de los dos CSV reales. La
misión producirá `plan.md`, `execution.md`, `verification.json`, evidencia,
CHANGELOG y documentación operativa. No se considerará terminada con
`verification.json` distinto de `passed`.

## Fuera de alcance

- Crear cursos o asignaturas Odoo ausentes.
- Consultar Moodle para descubrir automáticamente cursos o actividades.
- Inferir de forma fiable `quiz` frente a `assign` a partir del texto.
- Borrar mapas o actividades que ya no aparezcan en los CSV.
- Cambiar el algoritmo de cálculo o aplicación de notas de la libreta.
- Cambiar el criterio de modalidad del lote distinto de `HC`/`ONL`.
- Importación masiva desde una ruta indicada por un usuario web.

## Despliegue

La implementación no se publicará automáticamente. Commit, push a
`Dev_iRG`, actualización del addon en el servidor y cualquier importación real
de datos requerirán sus autorizaciones explícitas e independientes conforme a
la política del repositorio.
