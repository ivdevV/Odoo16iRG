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
se pueden crear nuevos Esquemas como archivo; las entregas parcial y final
continúan utilizando archivos.

## Actualización en beta

1. Actualizar el código de la rama autorizada en el servidor beta.
2. En Odoo, activar modo desarrollador.
3. Ir a **Aplicaciones**, pulsar **Actualizar lista de aplicaciones** y buscar
   `IRG TFM Convocatorias`.
4. Pulsar **Actualizar**. La versión esperada es `16.0.1.1.0`.
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
- Las versiones enviadas, preguntas congeladas y respuestas son inmutables.
- Los revisores solo pueden leer versiones enviadas; no pueden ver borradores ni
  modificar respuestas.
- No se crean correos, invitaciones, tokens de respuesta ni notificaciones al
  enviar. Solo se registra una nota interna no notificable en el chatter.
- Límites: 500 caracteres en texto corto, 20.000 en texto largo, 50 selecciones
  por pregunta y 100.000 caracteres totales por Esquema.

## Validación local de esta versión

Pasaron compilación Python, validación XML/manifest/ACL, 16 contratos estáticos,
`git diff --check` y escaneos de seguridad. Las suites Odoo y HTTP y TestSprite
no se lanzaron porque el usuario prohibió Docker en este ordenador y la política
del repositorio impide sustituir el entorno local por beta o producción.
