# Revisión de entregas TFM y sincronización con la libreta

## Contexto

`irg_tfm_convocatorias` conserva cada entrega parcial o final como una versión
inmutable de `irg.tfm.entrega`. El comentario actual de la entrega pertenece al
alumno y se captura durante la subida; no existe todavía una devolución formal
del revisor asociada a esa versión.

La calificación final ya se guarda en `tesis.model.points_fin`, con escala de 1
a 10 y el valor 0 como estado sin calificar. El módulo también depende de
`isep_gradebook`, pero `points_fin` no está vinculado actualmente a un resultado
de `app.gradebook.result`.

## Objetivos

1. Permitir que un Revisor TFM registre sobre cada versión parcial o final un
   estado de revisión y un comentario visible para el alumno.
2. Conservar el historial por versión sin volver mutable el archivo entregado.
3. Vincular la calificación final del expediente con el resultado de la
   asignatura TFM en la libreta del alumno.
4. Mantener `points_fin` y la calificación de la libreta sincronizados en ambas
   direcciones después de establecer el vínculo.
5. Resolver la asignatura TFM a partir de la configuración existente, sin
   depender del nombre ni del código de la asignatura.

## No objetivos

- No sustituir el cuestionario de Esquema ni añadir comentarios del revisor al
  Esquema en esta entrega.
- No modificar el archivo ni los metadatos históricos de `irg.tfm.entrega`.
- No enviar correos automáticos nuevos. La devolución se mostrará en el portal;
  el chatter conserva sus funciones actuales.
- No recalificar otras asignaturas ni cambiar la fórmula de promedios de
  `isep_gradebook`.
- No realizar un barrido masivo de calificaciones históricas durante el upgrade.

## Arquitectura elegida

### 1. Revisión independiente por versión

Se creará el modelo persistente `irg.tfm.entrega.revision`, con seguimiento de
chatter, y estos campos:

- `delivery_id`: entrega parcial o final revisada, obligatoria e inmutable.
- `state`: `pending`, `corrections` o `approved`.
- `comment`: devolución del revisor.
- `reviewed_by`: usuario que publicó la última decisión.
- `reviewed_at`: fecha y hora de la última decisión publicada.

Una restricción SQL permitirá como máximo una revisión por entrega. El historial
de versiones lo aporta `irg.tfm.entrega.version`; el historial de cambios de la
revisión queda en el tracking del nuevo modelo. La revisión no podrá eliminarse.

La ausencia de registro y el estado `pending` se presentan como **Pendiente de
revisión**. Pasar a `corrections` exigirá un comentario no vacío. Al guardar
`corrections` o `approved`, el servidor establecerá `reviewed_by` y
`reviewed_at`; esos metadatos no serán editables manualmente.
`create()` y `write()` rechazarán cualquier valor de cliente para `reviewed_by`
o `reviewed_at`, incluso `False`, valores correctos o contexto falsificado. Solo
el servidor los asigna con el actor original y su reloj. Tanto estos métodos
como la acción de apertura comprobarán etapa parcial/final y tesis activada
en servidor, incluso con acceso elevado; una regla de registro no sustituye
esta validación.

### 2. Experiencia del revisor

La pestaña **Entregas TFM** mostrará para cada versión:

- etapa, versión, archivo y comentario del alumno;
- estado de revisión y fecha de revisión;
- un botón **Revisar entrega** para versiones parciales y finales.

El botón abrirá la revisión existente o preparará una nueva para esa entrega.
El formulario mostrará el archivo, el alumno y la versión en solo lectura, y
permitirá modificar únicamente el estado y el comentario. Todas las acciones
protegidas validarán en servidor que el usuario pertenezca a **Revisor TFM** y
que la entrega sea parcial o final.

### 3. Experiencia del alumno

En el portal TFM, cada tarjeta de entrega mostrará:

- **Pendiente de revisión** mientras no haya una decisión publicada;
- **Requiere correcciones** o **Aprobada** cuando corresponda;
- comentario, revisor y fecha cuando exista una decisión publicada.

El alumno seguirá subiendo nuevas versiones dentro de la ventana vigente. No
podrá crear, editar ni eliminar revisiones por RPC o por rutas del portal. El
controlador solo leerá con `sudo()` después de resolver la entrega a través del
expediente propiedad del usuario autenticado.

## Resolución de la asignatura y de la libreta TFM

La resolución será determinista y reutilizará la configuración existente:

1. Partir de `tesis.model.course_id`, la matrícula exacta del expediente.
2. Leer `op.course.irg_tfm_channel_id` (**Canal TFM**).
3. Expandirlo a su familia HomeClass/Online mediante las funciones canónicas de
   `slide.channel` que ya proporciona `irg_tfm_convocatorias`.
4. Filtrar `op.course.subject_ids` y exigir exactamente una `op.subject` cuyo
   `slide_channel_id` pertenezca a esa familia.
5. Resolver exactamente una `app.gradebook.student` para el mismo alumno,
   curso y lote de la matrícula.
6. Resolver exactamente una `app.gradebook.subject` de esa libreta para la
   asignatura obtenida en el paso anterior.

Si cualquier paso produce cero o varios candidatos, se abortará el guardado con
un mensaje que indique qué debe corregirse: Canal TFM, asociación de la
asignatura, libreta o línea de asignatura. No se elegirá un candidato por nombre,
por orden ni con `limit=1`, y no se creará silenciosamente una línea que cambie
la estructura de una libreta existente.

## Vínculo y sincronización bidireccional

`app.gradebook.result` se ampliará con `irg_tfm_thesis_id`, indexado, de solo
lectura para la interfaz y único por expediente. Este campo es la identidad
estable del resultado de TFM; no se usará el texto de `name` o `description`
como clave.

### Desde el expediente TFM

Al guardar un `points_fin` distinto de 0:

1. se resolverán libreta y asignatura con las reglas anteriores;
2. si ya existe el resultado vinculado, se actualizará `scoring_total`;
3. si no existe y la línea no tiene resultados de examen, se creará uno con
   tipo `exam`, descripción **Calificación final TFM** y el vínculo al
   expediente;
4. si existe exactamente un examen sin vínculo en esa línea, se adoptará ese
   resultado para evitar duplicar una calificación histórica;
5. si existen varios exámenes sin vínculo, se abortará con un error de
   ambigüedad.

El valor 0 conservará la semántica existente de **sin calificar**: no creará un
resultado nuevo. Si ya existe un resultado vinculado y se vuelve a 0, ambos
campos quedarán en 0.

### Desde la libreta

Al crear o modificar un resultado de examen, el servidor solo lo ignorará si
demuestra que es ajeno al TFM (por ejemplo, no es examen o su línea queda fuera
de la familia configurada del Canal TFM). Cuando la resolución lo identifica
como candidato TFM, la selección, adopción o creación inicial del vínculo exige
la misma autorización, resolución cardinal, escala, política de normalización,
locks y relectura que el sentido directo: ningún error se captura para dejarlo
silenciosamente sin vincular. Tras resolver un único expediente activo para la
misma matrícula, establecerá `irg_tfm_thesis_id` y copiará `scoring_total` a
`points_fin`. Después de vincularlo, todo cambio en `scoring_total` actualizará
`points_fin`.

La sincronización cumplirá el contrato de seguridad y atomicidad siguiente en
ambas entradas, incluidos `tesis.model.create()` y los `create/write` de
resultados. No se modificará primero un extremo para resolver después el otro.

### Contrato de seguridad y atomicidad enmendado

1. **Frontera pública y autorización.** El contexto RPC es entrada no fiable.
   `irg_tfm_grade_sync_origin` solo puede describir origen o evitar recursión
   dentro de una operación ya autorizada; nunca habilita `sudo`, evita permisos,
   desactiva validaciones o permite enlaces/reasignaciones. Las entradas públicas
   rechazan marcadores de sincronización/defer reservados aportados externamente;
   no basta con comprobar la presencia de una clave para reconocer llamadas
   internas. El coordinador privado, no invocable por RPC, usa control de flujo
   Python del servidor y llamadas internas acotadas a la cadena `super`, sin
   introducir un bypass de autorización basado en contexto. Rechaza en `create`
   y `write` cualquier `irg_tfm_thesis_id` suministrado por el cliente, incluido
   `False`; únicamente el coordinador establece el vínculo calculado. La creación
   de tesis aplica los mismos controles sobre `points_fin`, incluidos defaults
   de contexto y valores explícitos 0, que su edición.
2. **Actor y privilegio mínimo.** Antes de resolver mediante lecturas elevadas o
   ejecutar escrituras elevadas, registrar el usuario original y comprobar sus
   ACL, reglas de registro y autorización de la operación de origen. En tesis,
   toda nota suministrada por el cliente exige Revisor TFM; la creación automática
   existente sin nota conserva sus permisos y su valor inicial sin calificar.
   En libreta, comprobar permisos de crear/escribir y reglas de los registros
   de origen y del destino propuesto antes de `super`, conservando los checks
   de `super` bajo ese mismo usuario. Para `create`, validar expresamente el
   alcance del padre propuesto, pues el resultado aún no existe. Solo el espejo
   ya resuelto se escribe con `sudo` estrecho, limitado al registro y campos
   necesarios. Un usuario de libreta no necesita convertirse en Revisor TFM;
   su permiso para el espejo nace de esa operación autorizada y del vínculo
   probado por el coordinador privado, nunca de un valor que el cliente elija.
   El espejo inverso no invoca la frontera pública `tesis.model.create/write`
   ni le pasa contexto reservado: dentro del mismo savepoint, el coordinador
   llama a un primitivo interno acotado a `super()` y a los campos del expediente
   que recibe explícitamente el actor ya autorizado y el vínculo ya verificado.
3. **Una jerarquía de locks antes de mutar.** Todas las entradas y las guardas
   de padres reúnen primero el conjunto completo afectado y bloquean por fases:
   `op.student.course` (matrícula/enrollment) → `tesis.model` →
   `app.gradebook.student` (libreta) → `app.gradebook.subject` (línea) →
   `app.gradebook.result` existentes. Dentro de cada fase se ordenan los IDs
   ascendentemente, también en lotes y operaciones multirregistro. La línea
   serializa creación/adopción aunque no haya fila de resultado. Si la tesis aún
   no existe, la matrícula serializa su creación; se adquieren todas las filas
   existentes en el orden común antes del primer `super().create()`, y las filas
   nuevas quedan protegidas por el padre bloqueado. Tras esperar locks se
   invalida y relee identidad, activación, notas, configuración y candidatos,
   y se repite la resolución completa. Si cambia el conjunto y exige un lock
   anterior, se aborta la operación; no se toma fuera de orden ni se reintenta
   sin límite. Se mantiene la unicidad SQL como defensa adicional.
4. **Compatibilidad de hooks.** Antes de implementar se traza la cadena real
   de `create/write/unlink`, normalización, recálculo y activación automática.
   Se incluyen todas las matrículas que los hooks puedan tocar antes de adquirir
   locks de tesis. `_irg_tfm_refresh_affected_enrollments()` se ejecuta una vez
   después de normalizar ambos extremos, con las matrículas ya bloqueadas.
   El defer interno no concede permisos ni puede activarlo un cliente para
   saltarse el refresco. Operaciones combinadas con cambio de convocatoria o
   configuración que activen otro orden de locks se rechazan antes de mutar
   cuando no puedan integrarse en el orden común. No se omiten validaciones,
   recálculos o efectos existentes para evitar la recursión.
5. **Identidad completa protegida en servidor.** Cuando exista vínculo, los
   `write/unlink` del resultado y sus padres rechazan cambios efectivos de
   `survey_type` (debe seguir `exam`), `gradebook_subject_id`, `irg_tfm_thesis_id`,
   `app.gradebook.subject.op_subject_id`, `gradebook_student_id`,
   `app.gradebook.student.admission_id`, identidad alumno/curso/lote de la
   admisión y de `op.student.course`, y `tesis.model.course_id`. Se protege
   también la modificación/borrado del padre por comandos One2many, cascadas
   o rutas indirectas que reasignen esa identidad. Los padres se bloquean según
   la misma jerarquía antes de comprobar si existe vínculo para evitar carreras
   con su creación. El mapeo íntegro y la tesis activada se revalidan antes de
   cada propagación. No se ofrece desvinculación ni eliminación histórica como
   remedio; una corrección de identidad exige una futura operación autorizada.
6. **Escala sin transformación.** Ambas entradas validan explícitamente un
   número finito con `math.isfinite` y `value == 0 or 1 <= value <= 10` antes
   de escribir o normalizar; rechazan negativos, fracciones entre 0 y 1, más de
   10, NaN e infinitos. Se rechazan atómicamente las configuraciones de libreta
   o plantilla que redondeen, limiten o transformen la nota solicitada: nunca
   se copia una nota transformada a la tesis ni se cambia la fórmula global.
   La prevalidación evalúa la política efectiva de normalización para ese valor
   (incluido 0); si no puede demostrar su conservación, rechaza el mapeo.
   Tras los hooks se invalida/relee el resultado efectivo y se comprueba
   igualdad con el valor solicitado y `points_fin`, sin tolerancia que oculte
   redondeo. Una diferencia produce `ValidationError` accionable para corregir
   escala/precisión/límites de la plantilla, dentro del mismo savepoint.
7. **Frontera atómica explícita.** Un savepoint del coordinador abarca resolución,
   validación, locks y relectura, ambos cambios, vínculo, efectos de hooks y
   auditoría. La resolución inicial y los locks preceden a cualquier mutación
   de negocio, incluida la creación inicial de tesis o resultado. Los errores
   de integridad o validación se propagan; no se capturan para continuar con
   cambios parciales. Una prueba captura el error en el llamador, fuera del
   savepoint interno pero dentro de la misma transacción, invalida caches y
   comprueba que nota de tesis, nota de resultado, vínculo, número de filas y
   mensajes siguen exactamente como antes. No depende del rollback global RPC.
8. **Auditoría transaccional.** Cada sincronización efectiva y adopción/creación
   de vínculo deja un mensaje en el chatter de la tesis con actor original,
   origen (`thesis`/`gradebook` calculado por el servidor), valores anteriores de
   ambos extremos, valor posterior y resultado vinculado (ID y referencia).
   Se conserva al actor aunque el espejo requiera `sudo`; el contexto no puede
   suplantarlo. Una operación fallida no deja mensaje de éxito. Repetir una
   escritura que no altera nota ni vínculo no duplica la auditoría.

### Condición de implementación y evidencia de la enmienda

Este contrato es condición previa de implementación y de una segunda revisión
independiente de seguridad. Ninguna clave de contexto, campo oculto, valor por
defecto RPC o restricción de vista es una capacidad de confianza. El único
origen interno es un coordinador Python privado, no invocable por RPC, que ya
recibió una operación pública autorizada. El contexto queda limitado a evitar
recursión o diferir un hook existente dentro de ese coordinador: nunca habilita
`sudo`, permisos, enlace, reasignación, validación, locks, `super()` o refresco.

| Hallazgo | Contrato que debe demostrar la implementación | Evidencia mínima |
| --- | --- | --- |
| Contexto falsificable | Rechazo de claves reservadas y enlaces de cliente en `create`/`write`, incluida creación de tesis | Casos de usuario interno, portal y libreta con contexto/enlace falsificado |
| `sudo()` prematuro | ACL, reglas y grupo del actor antes de lecturas/escrituras elevadas | Permiso denegado y contrato estático de orden |
| Carrera y orden inverso | Locks matrícula → tesis → libreta → línea → resultados, relectura tras lock | Dos cursores y contrato estático de orden |
| Identidad mutable | Guardas de resultado, línea, libreta, matrícula y tesis, incluso rutas indirectas | `write`, `unlink`, One2many/cascada y reasignación |
| Nota transformada | Escala finita `0` o `1..10` y rechazo de redondeo, clamp o transformación | Matriz de límites/NaN/infinito y plantilla transformadora |
| Rollback parcial | Savepoint de resolver, validar, bloquear, propagar y auditar | Error capturado con estado y chatter intactos |
| Auditoría | Chatter de tesis: actor, origen calculado, antes/después y resultado | Contenido, no duplicación y rollback |
| Metadatos de revisión | Metadatos solo de servidor y tesis/etapa validadas | Falsificación, tesis inactiva y etapa inválida |

## Permisos y auditoría

- `group_tfm_reviewer` tendrá lectura, creación y edición de
  `irg.tfm.entrega.revision`, sin permiso de borrado.
- Otros usuarios internos no obtendrán permisos sobre el nuevo modelo por el
  mero hecho de pertenecer a `base.group_user`.
- Los revisores podrán editar `points_fin` desde el expediente; el servidor
  comprobará el grupo, no solo la visibilidad del campo.
- Un usuario autorizado de la libreta podrá modificar el resultado TFM por los
  permisos existentes de `isep_gradebook`; la autorización se comprueba antes
  del `sudo` estrecho y los locks preceden también a `super().create/write()`.
  Ambas escrituras quedan dentro del savepoint descrito arriba.
- El alumno no recibirá ACL directas sobre revisiones ni resultados de libreta.
- Estado, comentario, revisor, fecha y cambios de calificación quedarán
  auditables mediante tracking/chatter de los modelos implicados.

Antes de implementar, un Security Advisor independiente revisará específicamente
las elevaciones `sudo()`, la propiedad portal, los cambios bidireccionales y la
protección frente a escrituras o borrados no autorizados.

## Compatibilidad y datos existentes

El upgrade del módulo creará el nuevo modelo y el campo de enlace, pero no
reescribirá entregas ni notas históricas en bloque:

- todas las entregas existentes comenzarán como pendientes de revisión;
- un `points_fin` existente se vinculará la siguiente vez que un revisor lo
  guarde;
- un único examen ya existente en la línea TFM podrá adoptarse al establecer el
  vínculo;
- las configuraciones ambiguas se corregirán explícitamente antes de sincronizar.

La versión del módulo se incrementará y el README explicará la configuración y
la prueba funcional.

## Errores y mensajes esperados

Los fallos de configuración usarán `ValidationError` y mensajes accionables, por
ejemplo:

- «El curso no tiene configurado Canal TFM.»
- «Debe existir una única asignatura del curso vinculada al Canal TFM.»
- «No se encontró una única libreta para el alumno, curso y lote.»
- «La libreta no contiene una única línea para la asignatura TFM.»
- «La asignatura TFM contiene varios exámenes sin vínculo; solicite una
  corrección autorizada de la configuración antes de continuar.»
- «La escala, precisión o límites de la libreta transformarían la nota TFM;
  corrija la plantilla para conservar exactamente la calificación solicitada.»

Ningún error parcial dejará `points_fin` y `scoring_total` con valores distintos,
porque el savepoint interno revierte toda la operación incluso si el llamador
captura la excepción y continúa dentro de la misma transacción.

## Estrategia de pruebas

El desarrollo seguirá RED–GREEN–REFACTOR.

### Pruebas de modelo

- creación y actualización de una revisión por un Revisor TFM;
- comentario obligatorio para `corrections`;
- rechazo de etapas no admitidas y de borrado;
- rechazo de creación/escritura por usuarios no autorizados;
- resolución de la asignatura con canal HomeClass y con su variante Online;
- errores por canal, asignatura, libreta o línea ausentes/ambiguos;
- creación idempotente, adopción inequívoca y rechazo de múltiples exámenes;
- sincronización `points_fin → scoring_total` y
  `scoring_total → points_fin` sin recursión;
- validación de escala, protección del vínculo y conservación transaccional ante
  errores.

La matriz de seguridad añade casos explícitos de contextos falsificados por
usuario interno, portal y usuario autorizado de libreta; enlace aportado por
cliente en `create/write`; tesis creada con nota/default de contexto; autor y
fecha de revisión falsificados; entrega de etapa no permitida o tesis inactiva;
y todas las reasignaciones/borrados de padres descritos. Ambos sentidos cubren
0, 1, 10, decimales, negativos, 0.5, 10.1, NaN e infinitos, redondeo/clamp de
plantilla, discrepancia efectiva inyectada después de los hooks y error capturado
sin cambios parciales. La auditoría debe conservar actor/origen/antes/después/ID
del resultado, no duplicarse por recursión ni existir tras rollback.

**Runtime futuro, dos cursores independientes:** escritura desde tesis frente
a escritura desde libreta; dos creaciones sin resultado; adopción frente a
creación; creación de tesis frente a activación automática; reasignación/borrado
del padre frente a primer vínculo; dos lotes con IDs en orden opuesto. Usar
barreras y tiempos límite, confirmar ausencia de deadlock, ausencia de duplicados,
relectura del estado ganador y nota/vínculo íntegros. Verificar el refresco de
matrícula/activación con la cadena real de hooks. Estas pruebas solo correrán
cuando se autorice el runtime desechable de `docker-compose.local.yml`, con
overlay del worktree, limpieza de fixtures y restauración del servicio original.

Los contratos estáticos revisarán orden de autorización/locks/escrituras,
savepoint, ausencia de bypass por contexto, todas las guardas de identidad,
validación finita, rechazo de normalización y contenido de auditoría. No prueban
ACL reales, semántica transaccional PostgreSQL, MRO ni concurrencia: esas
limitaciones permanecen explícitas mientras las pruebas runtime estén pendientes.

### Pruebas HTTP y vistas

- el portal muestra la revisión solamente al propietario de la entrega;
- el alumno no puede modificarla;
- cada versión muestra su estado y comentario correctos;
- la vista del expediente abre y guarda la revisión de la versión seleccionada;
- el árbol carga todos los campos usados para ordenar o mostrar estados.

Los checks de Python, XML y tests del módulo usarán `docker-compose.local.yml`
cuando esté autorizado. El cambio toca QWeb/portal, por lo que el contrato del
repositorio exige E2E con TestSprite después del resto de validaciones. Mientras
se mantenga la prohibición expresa de ejecutar Docker, esos checks dependientes
del runtime se registrarán como `skipped` con esa justificación y se aplicarán
validadores estáticos reproducibles.

## Despliegue y reversión

El despliegue requiere actualizar `irg_tfm_convocatorias`. No necesita un
barrido de datos previo. Tras actualizar, se comprobarán una entrega parcial,
una devolución visible en portal y ambos sentidos de la sincronización de nota.

La reversión de código no eliminará automáticamente la tabla de revisiones ni
el campo de enlace. Si fuera necesaria, se revertirá el commit y se actualizará
el módulo; los datos nuevos permanecerán en base de datos para evitar pérdida de
auditoría hasta que exista una decisión explícita de migración o borrado.
