# IRG TFM Convocatorias

## Esquema como cuestionario

El Esquema del Trabajo Final de Máster se completa desde MyCampus como un
cuestionario compacto de tres bloques:

1. **Datos y propuesta**.
2. **Planteamiento**.
3. **Resultados y fuentes**.

Cada bloque contiene varias preguntas. Nombre, correo y máster se completan con
la matrícula del expediente, pero el alumno puede corregirlos antes de enviar.
El alumno puede guardar un borrador, continuar después, revisar todas las
respuestas y enviar varias versiones mientras no tenga convocatoria.

Al enviar, la versión queda congelada. Los cambios posteriores en la plantilla
solo afectan a cuestionarios nuevos. Al asignar una convocatoria se cierran el
inicio, la edición y el envío del Esquema. Al retirarla, el alumno puede continuar
su borrador o crear una versión nueva.

Los Esquemas antiguos subidos como PDF/DOC/DOCX se conservan en lectura. Ya no
se pueden crear nuevos Esquemas como archivo; las entregas de observaciones
previas, parcial y final continúan utilizando archivos.

## Ventanas, notas y archivos (16.0.1.3.0)

- En la ficha del alumno, **Ventanas del alumno** cambia la apertura o el cierre
  de una etapa solo para ese expediente. Si la fecha queda vacía, vale la de la
  convocatoria.
- La convocatoria tiene fechas para **Observaciones previas a la entrega** y
  los pesos de **Nota del tutor**, **Nota del borrador** y **Nota de defensa**.
  Los tres pesos deben sumar 100. Cuando el revisor informa las tres notas, el
  punteo final se calcula y se sincroniza con la libreta como hasta ahora.
- En el esquema enviado, el revisor descarga las respuestas y puede subir un
  PDF, DOC o DOCX de retroalimentación. El alumno lo descarga en el portal.
- En la revisión de una entrega, el revisor puede adjuntar el archivo de
  observaciones. El alumno lo descarga cuando la revisión deja de estar pendiente.

## Actualización en beta

1. Actualizar el código de la rama autorizada en el servidor beta.
2. En Odoo, activar modo desarrollador.
3. Ir a **Aplicaciones**, pulsar **Actualizar lista de aplicaciones** y buscar
   `IRG TFM Convocatorias`.
4. Pulsar **Actualizar**. La versión esperada es `16.0.1.3.0`.
5. Confirmar que la aplicación **Encuestas** está instalada; es una dependencia
   declarada y Odoo debe instalarla automáticamente si falta.

## Editar las preguntas

1. Ir a **Encuestas**.
2. Abrir **Esquema preliminar y orientador del TFM**.
3. Editar títulos, explicaciones, obligatoriedad y opciones desde la pestaña de
   preguntas. No utilizar **Probar**, **Compartir** ni la URL nativa para recoger
   respuestas: esta encuesta funciona únicamente como plantilla del portal TFM.
4. Mantener exactamente tres secciones. Al editar una sección, conservar una
   clave técnica distinta en **Paso técnico TFM**:
   `proposal`, `approach` y `results`.
5. Mantener una sola pregunta con cada valor de **Dato automático TFM**:
   nombre del alumno, correo del alumno y máster de la matrícula. Estas tres
   preguntas deben ser de texto corto.
6. Mantener activado **Solo plantilla TFM**. Esta protección impide que las rutas
   nativas de Encuestas creen intentos o respuestas paralelas.

Tipos permitidos: texto corto, texto largo, selección única y selección múltiple.
La plantilla admite como máximo 100 preguntas y 100 opciones por pregunta.

## Prueba funcional con un alumno

Preparación:

- Utilizar una matrícula de máster elegible con progreso igual o superior al
  50 %, expediente TFM activo y sin convocatoria.
- Comprobar que el curso no sea un diplomado ni un lote presencial excluido.
- Acceder con un usuario Portal asociado exactamente a ese alumno.

Recorrido:

1. Entrar como alumno en `/campus` y abrir el máster.
2. Pulsar **Trabajo Final de Máster**.
3. En **Esquema**, pulsar **Comenzar cuestionario**.
4. Confirmar que nombre, correo y máster aparecen rellenados y que pueden
   editarse.
5. Cambiar uno de esos datos, responder el resto del primer bloque y pulsar
   **Siguiente**.
6. En el segundo bloque, responder varias preguntas y pulsar **Guardar
   borrador**. Volver a la página TFM y comprobar que aparece **Continuar
   borrador** y el último paso guardado.
7. Continuar, completar los tres bloques y pulsar **Revisar y enviar Esquema**.
8. Revisar el resumen y pulsar **Enviar Esquema**.
9. Confirmar que aparece **Versión 1 → Ver respuestas** y que ya no existe un
   formulario para subir el Esquema como archivo.
10. Sin convocatoria, iniciar y enviar otro cuestionario. Debe aparecer
    **Versión 2** sin alterar la versión 1.

Prueba de cierre:

1. Entrar como usuario interno con el grupo **Revisor TFM**.
2. Ir a **Tesis Management → Management → Revision Tesis** y abrir el expediente.
3. En la pestaña **Esquemas**, abrir cada versión y revisar respuestas, fecha y
   autor. Los borradores del alumno no deben aparecer.
4. Asignar una convocatoria al expediente.
5. Volver como alumno a Trabajo Final de Máster. Las versiones deben seguir
   visibles, pero no debe aparecer **Comenzar cuestionario** ni permitirse editar
   un borrador.
6. Retirar la convocatoria y comprobar que el cuestionario vuelve a abrirse.

## Seguridad y límites

- Todas las rutas requieren usuario autenticado y los POST validan CSRF.
- El expediente, borrador, preguntas y opciones se comprueban contra la matrícula
  del usuario en servidor.
- Una revisión de borrador evita que dos pestañas se sobrescriban silenciosamente.
- La revisión inicial se serializa explícitamente como `value="0"`; así el
  primer guardado conserva el control de concurrencia sin producir un falso
  conflicto.
- Las versiones enviadas, preguntas congeladas y respuestas son inmutables.
- Los revisores solo pueden leer versiones enviadas; no pueden ver borradores ni
  modificar respuestas.
- No se crean correos, invitaciones, tokens de respuesta ni notificaciones al
  enviar. Solo se registra una nota interna no notificable en el chatter.
- Límites: 500 caracteres en texto corto, 20.000 en texto largo, 50 selecciones
  por pregunta y 100.000 caracteres totales por Esquema.

Si un borrador sin convocatoria aparece en lectura después de actualizar desde
una versión anterior, confirme que el servidor ha cargado la última plantilla y
actualice el addon. El indicador del formulario se llama
`tfm_outline_editable` para no colisionar con el contexto `editable` reservado
por Website.

La vista **Esquemas → Respuestas** carga `sequence` como campo técnico invisible.
Debe conservarse mientras el árbol use `default_order="sequence, id"`; retirarlo
provoca un error de ordenación en memoria en el cliente web de Odoo 16.

## Revisión de entregas parcial y final

Cada versión de entrega (`irg.tfm.entrega`) es inmutable. El revisor no edita el
archivo: crea o actualiza una revisión (`irg.tfm.entrega.revision`) ligada a esa
versión. Solo el grupo **Revisor TFM** puede crear o editar revisiones; no se
pueden borrar. `reviewed_by` y `reviewed_at` los escribe el servidor.

Estados:

- **Pendiente de revisión**: el alumno ve el distintivo, no el comentario.
- **Requiere correcciones** y **Aprobada**: el alumno ve el estado y el
  comentario en `/campus/course/<course_id>/tfm`.

## Sincronización de la nota TFM

`tesis.model.points_fin` y el examen vinculado de la libreta
(`app.gradebook.result.scoring_total`) se mantienen iguales. El vínculo
`irg_tfm_thesis_id` lo calcula solo el servidor.

Configuración exacta por máster:

1. Un **Canal TFM** en el curso (`irg_tfm_channel_id`).
2. Una asignatura del curso cuyo `slide_channel_id` apunta a ese canal o a su
   pareja HomeClass/Online. No se resuelve por nombre, código ni `limit=1`.
3. Una libreta para el alumno, curso y lote exactos.
4. Una línea de libreta para esa asignatura TFM.
5. Plantilla de libreta en escala 10, sin redondeo ni recorte que transforme la
   nota. La nota aceptada es un número finito `0` o `1..10`.

Solo un **Revisor TFM** puede escribir `points_fin`. Un usuario de libreta con
permiso de administración de `isep_gradebook` puede crear o editar el examen
vinculado; ese cambio vuelve al expediente.

### Examen en la línea TFM sin expediente activo

A partir de `16.0.1.2.0`, crear un examen en la asignatura TFM exige una
matrícula única y un expediente TFM **activo** para esa matrícula. Si faltan,
Odoo rechaza la operación con:

- `No se encontró una única matrícula para el alumno, curso y lote de la libreta.`
- `No se encontró un único expediente TFM activo para la matrícula de la libreta.`

Remedio: configure el Canal TFM, active el expediente (progreso ≥ 50 % o
activación interna) y deje una sola línea/examen candidato. Un segundo examen
sin vínculo en la misma línea también se rechaza: hay que editar el vinculado.

No se pueden cambiar a la vez la matrícula (`course_id`) y la convocatoria TFM
del expediente, ni escribir en el mismo lote resultados TFM y no TFM.

## Prueba beta de revisión y nota

Preparación: módulo actualizado a `16.0.1.2.0`, máster con Canal TFM y asignatura
puente, alumno con expediente activo, convocatoria y una entrega parcial.

1. Como **Revisor TFM**, abrir el expediente en **Tesis Management → Management
   → Revision Tesis**.
2. En **Entregas TFM**, pulsar **Revisar entrega** de la versión parcial.
3. Poner estado **Requiere correcciones**, escribir un comentario y guardar.
4. Como el alumno dueño, abrir `/campus/course/<course_id>/tfm` y comprobar que
   ve el estado y el comentario; otro alumno no debe verlos.
5. Como revisor, escribir `points_fin` (por ejemplo `8.5`).
6. En la libreta del alumno, la línea de la asignatura TFM debe mostrar un
   examen con la misma nota.
7. Como usuario de libreta, cambiar ese examen a `9.0` y volver al expediente:
   `points_fin` debe ser `9.0`. El chatter del expediente registra la
   sincronización.

## Validación local de esta versión

Pasaron AST Python, XML bien formado, contratos estáticos de revisión/portal/sync
(incluidos create list-safe y orden de bloqueo), `compileall` y `git diff --check`.
Review independiente: sin hallazgos bloqueantes. Validación independiente
`passed`. Las suites Odoo, la concurrencia de dos cursores y TestSprite no se
lanzaron porque el usuario prohibió Docker en este ordenador y la política del
repositorio impide sustituir el entorno local por beta o producción.
