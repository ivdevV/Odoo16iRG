# Diseño: Esquema TFM mediante encuesta versionada

## Objetivo

Sustituir, para el nuevo flujo TFM, la subida de archivos de la etapa Esquema por
un cuestionario cuya plantilla se administra con Encuestas de Odoo. El alumno
podrá guardar un borrador, terminar varias versiones antes de recibir convocatoria
y consultar sus envíos. El revisor podrá abrir cada versión desde `tesis.model` y
ver la copia inmutable de las preguntas y respuestas tal como fueron enviadas.

La Entrega parcial y la Entrega final mantienen el flujo actual de archivos. Los
Esquemas históricos que ya existan como archivos tampoco se modifican ni se
eliminan.

## Decisiones aprobadas

- Existe una sola encuesta TFM configurada globalmente para todos los másteres.
- Las preguntas se administran con la aplicación nativa **Encuestas** de Odoo.
- Nombre, correo y máster se rellenan automáticamente, pero el alumno puede
  editarlos antes de enviar.
- El cuestionario se presenta como el formulario portal de solicitud de
  Prácticas: tres pasos temáticos con varias preguntas por paso, no una pregunta
  por página.
- Al pulsar **Siguiente** se guardan en servidor las respuestas del paso actual;
  **Anterior** permite revisarlas sin perder el borrador.
- Solo puede existir un borrador activo por expediente; al volver se continúa
  desde el punto guardado.
- El número de versión se asigna únicamente al completar el cuestionario.
- Se admiten múltiples versiones completadas mientras no haya convocatoria.
- Cada versión conserva una copia inmutable del texto, tipo y respuesta de cada
  pregunta aunque la plantilla se edite posteriormente.
- La plantilla se congela al crear el borrador: editar o borrar preguntas en
  Encuestas solo afecta a borradores nuevos y nunca altera uno ya iniciado.
- No se crean intentos nativos `survey.user_input`, enlaces por token ni rutas
  públicas de Encuestas; el portal TFM guarda sus respuestas en modelos privados.
- El revisor consulta las respuestas en modo lectura; no las edita ni califica.
- Asignar convocatoria bloquea el borrador y nuevos envíos. Retirarla permite
  continuar el borrador existente o crear una versión nueva.
- No se añaden correos automáticos.

## Plantilla inicial

El módulo crea una encuesta global denominada **Esquema preliminar y orientador
del TFM**. La definición se carga como dato `noupdate` para que una actualización
del addon no sobrescriba las ediciones realizadas en Odoo.

La encuesta contiene inicialmente estas preguntas, tomadas del formulario de
Google aportado como referencia:

1. **Nombre y apellidos** — texto corto, obligatorio, prerrelleno desde el alumno.
2. **Correo electrónico personal** — texto corto, obligatorio, prerrelleno desde
   el alumno.
3. **Máster en el que estudia** — texto corto, obligatorio, prerrelleno desde la
   matrícula exacta que originó el expediente.
4. **Título provisional del TFM** — texto corto, obligatorio. Ayuda: «Formula un
   título claro y preciso que refleje el tema central del TFM y anticipe la
   finalidad o el enfoque principal del trabajo».
5. **Modalidad del TFM** — selección múltiple obligatoria con:
   - Revisión bibliográfica.
   - Elaboración de recurso didáctico para la intervención.
   - Diseño, aplicación y evaluación de un programa de intervención.
   - Diseño y evaluación de un programa de intervención (sin aplicación
     práctica).
6. **Planteamiento del problema** — texto largo, obligatorio. Ayuda: «Describe
   brevemente el fenómeno o necesidad que deseas abordar, su relevancia
   profesional o social, el contexto donde se presenta y las principales razones
   que justifican su estudio o intervención».
7. **Objetivo general** — texto largo, obligatorio. Ayuda: «Redacta un enunciado
   que exprese la meta principal de tu trabajo, indicando qué pretendes lograr o
   aportar con el desarrollo del TFM».
8. **Pregunta de investigación (solo modalidad 1)** — texto largo, opcional, con
   el ejemplo del formulario original como ayuda.
9. **Resultados esperados** — texto largo, obligatorio. Ayuda: «Describe los
   logros o aportes que prevé alcanzar con su TFM y cómo con ellos podría mejorar
   la práctica profesional, el aprendizaje o el bienestar de los destinatarios».
10. **Referencias bibliográficas** — texto largo, obligatorio. Ayuda: «Indique al
    menos cinco fuentes académicas en formato APA 7.ª edición que utilizaría en su
    trabajo».

Las tres preguntas prerrellenables reciben una marca técnica independiente de su
título visible. Así, el administrador puede cambiar el texto sin romper el
origen de los datos. La encuesta TFM válida debe conservar exactamente una
pregunta para cada origen: nombre, correo y máster. Si falta o se duplica una,
Odoo impedirá iniciar un cuestionario y mostrará una explicación al usuario
interno responsable de la configuración.

## Configuración global

Se añade a Ajustes una referencia global **Encuesta de Esquema TFM**, respaldada
por `ir.config_parameter`. Durante la instalación se selecciona la plantilla
incluida. Un administrador puede editarla en Encuestas o sustituirla por otra,
siempre que cumpla el contrato de las tres preguntas prerrellenables.

La encuesta funciona como cuestionario sin puntuación, certificación ni límite
de intentos propio. La plantilla y sus preguntas se administran con los modelos
nativos de Encuestas, pero el alumno la responde dentro de la página TFM mediante
un formulario portal propio inspirado en la solicitud de Prácticas. Así se evita
la navegación nativa de una pregunta por página sin perder la edición de
preguntas desde Odoo.

La presentación se divide en tres pasos con varias preguntas relacionadas:

1. **Datos y propuesta**: nombre, correo, máster, título provisional y modalidad.
2. **Planteamiento**: planteamiento del problema, objetivo general y pregunta de
   investigación.
3. **Resultados y fuentes**: resultados esperados, referencias bibliográficas y
   revisión previa al envío.

Los pasos se derivan de secciones técnicas de la encuesta. Cada sección recibe
una clave inmutable y única (`proposal`, `approach` o `results`), independiente de
su título visible, para que pueda renombrarse sin romper el flujo. Debe existir
exactamente una sección de cada clave; una pregunta nueva queda dentro de la
sección donde se añada. El portal renderiza todos los campos
del paso actual en una sola pantalla. **Siguiente** valida las preguntas
obligatorias de ese paso y persiste sus respuestas; **Anterior** no descarta lo
ya guardado. En el último paso aparecen **Guardar borrador** y **Revisar y enviar
Esquema**. Antes del envío definitivo se muestra un resumen completo editable por
pasos. El control de borradores, versiones y convocatoria pertenece al
expediente TFM y no a las opciones genéricas de reintento de exámenes. El texto
que todavía no se haya guardado o confirmado con **Siguiente** no se considera
persistido.

## Modelos y versionado

### `irg.tfm.esquema`

Representa un borrador o una versión completada:

- `thesis_id`: expediente propietario, con borrado restringido.
- `survey_id`: plantilla utilizada.
- `version`: `0` mientras es borrador y correlativo positivo al completar.
- `state`: `draft` o `done`.
- `revision`: correlativo de edición usado para rechazar guardados obsoletos de
  otra pestaña.
- `current_step`: último paso persistido.
- `started_by`, `started_at`, `submitted_at`.
- `question_ids`: copia congelada de las preguntas, opciones y respuestas.

Una restricción única `(thesis_id, version)` garantiza un solo borrador con
versión cero y una sola fila por versión completada. El expediente se bloquea
antes de crear/reutilizar el borrador y antes de asignar el siguiente número para
evitar carreras entre pestañas o peticiones simultáneas.

### `irg.tfm.esquema.pregunta`

Cada borrador copia, por orden de presentación:

- clave del paso y título original de su sección;
- texto y descripción originales de la pregunta;
- tipo original de pregunta;
- indicación de obligatoriedad;
- origen de prerrelleno, si existe;
- opciones congeladas mediante `irg.tfm.esquema.opcion`;
- respuesta textual o las opciones seleccionadas.

Las preguntas congeladas se crean con el borrador y son editables únicamente por
los métodos privados de guardado mientras el padre está en estado `draft`. Al
finalizar se vuelven inmutables junto con sus respuestas; no dependen de que la
pregunta o sus opciones sigan existiendo en la plantilla.

### Extensiones nativas

- `survey.question` incorpora el origen opcional de prerrelleno TFM.
- Las filas de sección de `survey.question` incorporan la clave técnica de paso
  TFM. Las preguntas ordinarias admiten los tipos `char_box`, `text_box`,
  `simple_choice` y `multiple_choice`; cualquier otro tipo bloquea la creación de
  un borrador con un mensaje de configuración.
- `tesis.model` expone sus Esquemas versionados y considera que hay Esquema válido
  cuando existe al menos una versión de encuesta completada o un Esquema legacy
  en archivo.

## Flujo del alumno

1. Al alcanzar el 50 %, la tarjeta TFM continúa apareciendo como ahora.
2. Sin convocatoria, la sección Esquema muestra **Comenzar cuestionario** o
   **Continuar borrador**.
3. Al comenzar se crea o recupera el único borrador del expediente, se congela la
   plantilla vigente y se rellenan nombre, correo y máster desde `op.student` y
   `op.student.course`.
4. El alumno puede modificar esos valores y responder en tres pasos, con varias
   preguntas visibles en cada pantalla, dentro del mismo diseño portal de TFM.
5. Cada **Siguiente** guarda las respuestas del paso y la posición del borrador.
   **Guardar borrador** permite hacerlo explícitamente sin avanzar. Volver a
   MyCampus no crea otro intento y **Continuar borrador** vuelve al último paso
   guardado.
6. Cada guardado envía la revisión conocida del borrador. El servidor la compara
   y la aumenta bajo bloqueo; una pestaña antigua recibe un aviso y no sobrescribe
   respuestas más recientes.
7. Después de revisar el resumen, al enviar el servidor vuelve a comprobar
   propiedad, respuestas obligatorias y ausencia de convocatoria,
   asigna la versión correlativa y crea la copia histórica.
8. La página TFM lista todas las versiones completadas con fecha y permite ver sus
   respuestas en modo lectura.
9. Tras completar una versión aparece **Enviar nueva versión del Esquema**, que
   genera otro borrador únicamente cuando el alumno decide usarlo.
10. Con convocatoria, las versiones siguen visibles pero no se puede iniciar,
   continuar ni finalizar un cuestionario.
11. Al retirar la convocatoria, el borrador anterior vuelve a estar disponible.

Los tres datos automáticos son sugerencias iniciales, no campos sincronizados:
si el alumno los cambia, la versión conserva lo que escribió. Un cambio posterior
en su ficha académica no altera una versión ya enviada.

## Flujo del revisor

El formulario de `tesis.model` incorpora una pestaña **Esquemas**, visible solo
para el grupo explícito **Revisor TFM**, con:

- número de versión;
- estado;
- encuesta utilizada;
- alumno/autor;
- fecha de inicio y envío;
- acceso a **Ver respuestas**.

El formulario de cada versión presenta las preguntas y respuestas históricas en
orden. Administrar la plantilla en Encuestas no concede por sí solo permiso para
leer respuestas TFM.

Los borradores pueden mostrarse al revisor solo como estado y fecha, sin exponer
respuestas parciales. La advertencia no bloqueante al asignar convocatoria solo
se omite cuando existe una versión completada o un Esquema legacy; un borrador no
cuenta como entrega.

## Compatibilidad con Esquemas anteriores

Las filas `irg.tfm.entrega` de etapa `outline` y sus adjuntos permanecen
inmutables. Se muestran en un bloque separado **Esquemas anteriores en archivo**
tanto al alumno como al revisor. No se crean intentos de encuesta artificiales ni
se intenta convertir documentos a respuestas.

Entrega parcial y Entrega final siguen utilizando archivos y el modelo
`irg.tfm.entrega` sin cambios funcionales.

## Seguridad

- El alumno no recibe ACL directas de escritura sobre Esquemas, preguntas
  congeladas, opciones ni expedientes.
- Las rutas parten de la cadena autenticada
  `res.users → op.student → op.student.course → tesis.model`.
- Crear o recuperar borrador exige propiedad exacta, curso no diplomado,
  activación TFM y ausencia de convocatoria.
- No existen `survey.user_input` ni tokens para este flujo. Todas las mutaciones
  usan rutas `POST`, `auth='user'`, `csrf=True`; las rutas GET solo leen.
- Guardado y finalización usan el mismo orden de bloqueo que las entregas:
  convocatoria vigente cuando exista, curso y expediente; después releen
  matrícula, convocatoria, borrador y revisión. Si el revisor asignó convocatoria
  mientras el alumno respondía, el envío se rechaza y el borrador queda guardado.
- `step`, pregunta y opción se derivan y validan contra el borrador congelado; no
  se confía en IDs aislados del navegador. `char_box` admite hasta 500 caracteres,
  `text_box` hasta 20.000, cada pregunta puede definir como máximo 100 opciones y
  seleccionar como máximo 50, la plantilla admite hasta 100 preguntas y el total
  de respuestas textuales de un Esquema no supera 100.000 caracteres. QWeb
  siempre usa `t-esc` para texto del alumno.
- Las versiones completadas, preguntas y opciones históricas no admiten `write`,
  `unlink` ni `copy`; los cambios se expresan creando otra versión.
- Solo el grupo Revisor TFM lee versiones terminadas y respuestas. La capacidad
  de editar la plantilla depende de los grupos estándar de Encuestas.
- No se registra el contenido de las respuestas en chatter, solo versión y fecha.
  La entrada se crea directamente como mensaje interno no notificable, sin pasar
  por `message_post`; finalizar no crea `mail.notification` ni `mail.mail`.
- El flujo no genera enlaces anónimos, invitaciones ni correos.

## Errores y mensajes

- Encuesta global ausente: «No está configurada la encuesta de Esquema TFM».
- Preguntas automáticas incompletas o duplicadas: mensaje de configuración para
  el administrador; el alumno recibe un aviso genérico sin detalles internos.
- Convocatoria asignada durante el cuestionario: «El Esquema se ha cerrado porque
  ya tienes una convocatoria asignada».
- Intento de otro usuario, curso o expediente: recurso no encontrado.
- Carrera de versión: se reintenta una vez bajo savepoint; si persiste, se pide
  volver a enviar sin crear una versión parcial.

## Pruebas

La implementación seguirá TDD e incluirá:

- creación de la plantilla y las 10 preguntas con tipos y obligatoriedad;
- renderizado de tres pasos temáticos con varias preguntas por pantalla;
- guardado de las respuestas y del paso actual al pulsar **Siguiente** o
  **Guardar borrador**;
- validación por paso y revisión completa antes del envío;
- validación de las tres fuentes de prerrelleno;
- nombre, correo y máster automáticos pero editables;
- creación y reanudación de un único borrador congelado;
- edición o borrado de la plantilla sin alterar un borrador iniciado;
- asignación de versiones solo al completar;
- concurrencia y unicidad de borrador/versiones;
- rechazo de guardados obsoletos desde dos pestañas;
- múltiples versiones antes de convocatoria;
- bloqueo de inicio, guardado y finalización después de convocatoria;
- reapertura al retirar convocatoria;
- snapshot inmutable después de editar o borrar preguntas/opciones de plantilla;
- vista del alumno y del revisor;
- ocultación de respuestas parciales al revisor;
- aislamiento entre alumnos, cursos, expedientes y tokens;
- ausencia de `survey.user_input`, rutas nativas y tokens alternativos;
- ACL del grupo Revisor TFM y cero correos generados;
- compatibilidad de Esquemas legacy y advertencia de convocatoria;
- ausencia de regresiones en Entrega parcial, Entrega final y eLearning.

El cambio afecta controladores y QWeb, por lo que el contrato del repositorio
activa TestSprite. En este ordenador no se ejecutará Docker por instrucción
expresa del usuario; Odoo runtime y TestSprite quedarán como `skipped` justificado
y deberán repetirse contra una base local desechable en un equipo autorizado.
Nunca se utilizará beta o producción como destino de TestSprite.

## Despliegue

La actualización añade la dependencia directa `survey`, crea la plantilla y la
selecciona como encuesta global únicamente si no existe ya una configuración.
No altera convocatorias, expedientes, entregas ni respuestas actuales. Después de
desplegar será necesario actualizar el addon **IRG TFM Convocatorias** y revisar
la plantilla desde Encuestas antes de probar con un alumno.
