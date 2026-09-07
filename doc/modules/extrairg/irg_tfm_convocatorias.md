# irg_tfm_convocatorias

**Categoría:** extrairg

**Versión:** 16.0.1.0.1

**Licencia:** LGPL-3

**Instalable:** Sí

**Autor:** IRG

**Depende de:** `base`, `mail`, `openeducat_core`, `isep_student_filter`, `isep_gradebook`, `website_slides`, `isep_tesis_model`, `irg_course_portal_tiles`, `irg_course_portal_tiles_diplomado_hide`, `irg_batch_slide_restrictions`, `irg_practice_slide_restrictions`, `irg_elearning_editable_sections`, `irg_auto_enroll_cron_robust`

---

## Objetivo

Automatiza el inicio y las entregas del **Trabajo Final de Máster (TFM)** a partir del progreso académico. Al alcanzar el 50 % en una matrícula elegible, el módulo crea un expediente interno `tesis.model` y muestra una tarjeta de TFM dentro del curso en MyCampus. El alumno puede enviar primero el **Esquema**; después, un revisor asigna una convocatoria y se habilitan las ventanas de **Entrega parcial** y **Entrega final**, además del canal eLearning configurado para el máster.

Este flujo sustituye, para las matrículas activadas por el módulo, las antiguas secciones 1–5 por tres etapas versionadas:

1. Esquema.
2. Entrega parcial.
3. Entrega final.

## Flujo funcional

### 1. Activación al 50 %

Se crea una única ficha `tesis.model` por `op.student.course` cuando se cumplen simultáneamente estas condiciones:

- `completion_porc >= 50`, usando el progreso real calculado por `isep_student_filter`.
- El curso tiene activado `activate_tesis`.
- El código del lote cumple uno de los cortes admitidos.

| Modalidad o familia | Primer lote incluido | Observaciones |
| --- | --- | --- |
| HomeClass | `HC2511` | Admite `HC` desde noviembre de 2025. |
| Neurologopedia | `MONLHC2601` | Usa el corte especial desde enero de 2026. |
| Online | `ONL2602` | Admite `ONL` desde febrero de 2026. |
| Presencial | — | Todo código que contenga `PRS` queda excluido. |

El parser también rechaza meses inválidos. La activación se intenta inmediatamente al crear o actualizar la matrícula y después de crear, modificar o eliminar una calificación `app.gradebook.result`. Antes de decidir, el módulo recalcula y persiste la nota final afectada, invalida el progreso y serializa la comprobación por matrícula. Como respaldo existe un cron horario. La activación es irreversible: si el progreso baja después del 50 %, el expediente y la tarjeta continúan activos.

`completion_porc` no es una columna almacenada ni admite búsquedas SQL. Por eso el cron pagina matrículas de cursos TFM y calcula el porcentaje de cada candidata en Python. El progreso tampoco distingue lotes: si existen matrículas duplicadas del mismo alumno en el mismo curso, todas se evalúan y después se aplica a cada una su propio corte de lote. Operativamente debe mantenerse una sola matrícula válida por alumno y curso.

La ficha se crea en estado borrador con nombre, correo, matrícula y fecha de activación. La operación es idempotente y una restricción PostgreSQL impide dos expedientes para la misma matrícula, incluso ante activaciones concurrentes.

### 2. Esquema antes de la convocatoria

La tarjeta **Trabajo Final de Máster** aparece dentro del curso en MyCampus y abre:

```text
/campus/course/<course_id>/tfm
```

Mientras el expediente no tenga convocatoria, el alumno solo puede:

- enviar un Esquema;
- añadir un comentario opcional;
- consultar y descargar todas las versiones que haya enviado.

El alumno puede añadir nuevas versiones, pero no editar ni borrar el historial. La Entrega parcial, la Entrega final y el acceso TFM al canal eLearning todavía no se habilitan.

### 3. Revisión y asignación de convocatoria

El revisor abre la ficha desde el menú backend existente de revisión de tesis. En ella puede:

- revisar la pestaña **Entregas TFM**;
- completar los campos heredados **Tipo de Tesis** (`type_thesis`) y **Comentario/Información adicional** (`application_description`);
- seleccionar una convocatoria activa en **Convocatoria TFM**.

Si todavía no existe un Esquema, la asignación se permite, pero se registra una advertencia en el chatter. La asignación también queda registrada en el chatter.

Para asignar una convocatoria, el curso debe tener configurado un canal TFM. Al guardar:

- se cierra el formulario de Esquema;
- se sincroniza la membresía del alumno en el canal;
- se aplican las fechas de la convocatoria;
- el portal muestra Entrega parcial, Entrega final y el enlace eLearning;
- el filtrado eLearning usa siempre la convocatoria vigente del expediente.

### 4. Entrega parcial y final

Las ventanas se definen con campos `Date`. El servidor obtiene el día actual en la zona horaria `Europe/Madrid` y considera inclusivos los dos extremos:

```text
fecha_apertura <= hoy_en_Madrid <= fecha_cierre
```

Si falta cualquiera de las dos fechas, la ventana permanece cerrada. El control se repite en servidor durante la subida; ocultar o mostrar el formulario no es la única protección.

Cada entrega conserva:

- expediente y etapa;
- convocatoria histórica;
- archivo y comentario;
- autor y fecha/hora;
- número de versión;
- indicación y motivo cuando fue creada como excepción interna.

El versionado se calcula por expediente, etapa y convocatoria histórica. Por ello, cambiar la convocatoria inicia una secuencia independiente para las nuevas entregas sin eliminar las anteriores.

### 5. Cambio o retirada

- **Cambiar convocatoria:** seleccione otra convocatoria activa en el expediente. Se aplican el nuevo contenido y las nuevas fechas; todas las versiones anteriores siguen visibles en modo lectura con su convocatoria original.
- **Retirar convocatoria:** vacíe el campo `irg_tfm_convocation_id` del expediente. Se retira la referencia TFM a la membresía eLearning, se cierran las entregas parcial/final y el Esquema vuelve a admitir versiones. La tarjeta permanece visible.
- **Archivar la convocatoria del catálogo:** no equivale a retirarla del expediente. Una convocatoria archivada no admite nuevas entregas ni puede asignarse, pero el Esquema continúa cerrado mientras el expediente conserve esa referencia. Para reabrir el Esquema se debe retirar expresamente la convocatoria del expediente.

Las entregas históricas y sus adjuntos nunca se borran durante estos cambios.

## Configuración

### Curso y canal TFM

En el formulario del máster (`op.course`):

1. Active **Revisión de tesis** (`activate_tesis`) si el curso participa en el flujo.
2. Seleccione un **Canal TFM** (`irg_tfm_channel_id`).

Se recomienda un canal TFM claramente identificado por máster. Si un alumno queda asociado de forma ambigua a más de una matrícula para el mismo canal, el acceso exclusivo falla de forma cerrada.

Cambiar el canal de un curso vuelve a conciliar las membresías de sus expedientes. El módulo no se apropia de membresías creadas por otros procesos: una membresía activa ajena puede seguir dando acceso genérico al canal, pero no se marca, modifica ni archiva como TFM.

### Catálogo global de convocatorias

Los usuarios internos gestionan **Convocatorias TFM** desde la configuración del módulo de tesis. Cada registro contiene:

- nombre;
- código global único, normalizado en mayúsculas, por ejemplo `CONV0326`;
- estado activo;
- apertura y cierre de Entrega parcial;
- apertura y cierre de Entrega final.

La fecha de apertura no puede ser posterior a la de cierre. Las convocatorias archivadas quedan disponibles como referencia histórica, pero no se pueden asignar ni recibir entregas nuevas.

### Categorías eLearning

En el contenido del canal, el campo **Convocatorias TFM** solo puede configurarse en registros `slide.slide` que sean categorías:

- categoría sin convocatorias: contenido común;
- categoría con una o varias convocatorias: contenido exclusivo de esas convocatorias;
- los materiales heredan la restricción de su categoría o de su padre.

El filtrado se combina con las restricciones existentes de lote y prácticas. Las categorías y materiales no autorizados se ocultan en listados y sidebar, y el controlador vuelve a validar antes de entregar el contenido o marcarlo como visto. Una URL directa no evita la restricción.

## Uso operativo

### Alumno en MyCampus

1. Entra al curso cuando la matrícula ya alcanzó el hito del 50 %.
2. Abre la tarjeta **Trabajo Final de Máster**.
3. Envía una o varias versiones del Esquema mientras no haya convocatoria.
4. Tras la asignación, consulta las fechas y entra al contenido eLearning.
5. Envía Entrega parcial y Entrega final dentro de sus ventanas.
6. Conserva acceso de lectura a todas sus versiones y convocatorias históricas.

La entrada heredada **Revisión de tesis** desaparece de `/my`. Las rutas antiguas de creación, listado, detalle, aceptación, rechazo, envío, descarga, borrado y comentario quedan neutralizadas: las consultas se redirigen a `/campus` cuando corresponde y las mutaciones o accesos a documentos devuelven recurso no encontrado.

### Revisor y administrador

1. Configura el canal TFM del curso y el catálogo global de convocatorias.
2. Etiqueta las categorías exclusivas del canal con una o varias convocatorias.
3. Revisa el Esquema y completa tipo y descripción en el expediente.
4. Asigna, cambia o retira la convocatoria desde el formulario `tesis.model`.
5. Consulta el historial inmutable en la pestaña **Entregas TFM** y la trazabilidad en chatter.

Las excepciones fuera de plazo solo pueden crearlas usuarios internos mediante el servicio `_irg_create_delivery_exception`. Requieren un motivo no vacío, generan una versión nueva y dejan mensaje en chatter. Esta versión no incorpora un botón específico para la excepción; una acción interna que lo invoque debe aportar archivo, MIME, etapa, motivo y comentario opcional. La excepción no permite reabrir un Esquema después de asignar convocatoria y tampoco permite usar una convocatoria archivada.

## Seguridad e integridad

- La resolución portal sigue la cadena autenticada `res.users → op.student → op.student.course → tesis.model → irg.tfm.entrega`. Si existe cero o más de un candidato, el acceso se deniega.
- Las subidas usan `POST` con CSRF. El alumno no recibe ACL directa para crear, editar o borrar expedientes, convocatorias o entregas.
- Solo se aceptan PDF, DOC y DOCX no vacíos de hasta **20 MiB de bytes crudos**.
- La extensión, el MIME declarado y el contenido real deben coincidir. Se valida la estructura PDF, el contenedor OLE/FIB de Word para DOC y la estructura ZIP/XML de Word para DOCX.
- Los DOCX tienen límites de entradas, directorio central, tamaño descomprimido, ratio de compresión y lectura XML; se rechazan ZIP64, multidisco, XML con DTD/entidades y archivos genéricos renombrados.
- Cada `ir.attachment` es privado y queda ligado exclusivamente a su `irg.tfm.entrega`. La descarga comprueba de nuevo propiedad, vínculo, tipo y privacidad, y envía `Content-Disposition` seguro y `X-Content-Type-Options: nosniff`.
- Entregas y adjuntos son inmutables; no admiten edición o borrado posterior. Las excepciones crean otra versión, nunca alteran la anterior.
- Convocatorias, expedientes y snapshots históricos usan restricciones y relaciones `ondelete='restrict'` donde corresponde.
- La asignación y la subida serializan la configuración con el orden de bloqueo `convocatoria → curso → expediente`, releen el estado y usan constraints para resolver carreras de versión o activación.
- Las membresías creadas por TFM guardan procedencia por expediente. Una fila ajena no se reactiva, altera ni archiva; una fila TFM solo se archiva cuando ya no tiene referencias ni señales académicas externas.

## Cron e idempotencia

El cron **IRG: activar fichas TFM elegibles** se ejecuta cada hora como superusuario. Procesa como máximo 500 matrículas por ejecución y conserva el cursor en:

```text
irg_tfm_convocatorias.activation_cursor
```

Al llegar al final reinicia el cursor a cero. Cada candidata vuelve a pasar las reglas de curso, progreso y lote antes de crear el expediente. La restricción única sobre `tesis.model.course_id` y el savepoint de la creación hacen que reintentar sea seguro.

## Correos y trazabilidad

El flujo nuevo no define plantillas ni crea mensajes `mail.mail`. La creación automática del expediente usa el contexto `irg_tfm_auto_activation` para suprimir específicamente el correo heredado de `isep_tesis_model`. Las asignaciones, retiradas, advertencias y excepciones se registran en el chatter del expediente.

## Instalación y actualización

Antes de instalar:

1. Instale todas las dependencias declaradas en el manifest.
2. Compruebe que está instalado `isep_student_filter`, proveedor de `op.student.course.completion_porc`, e `isep_gradebook`.
3. Resuelva cualquier duplicado existente de `tesis.model` por matrícula.
4. Haga copia de seguridad y pruebe primero en una base desechable.

El `pre_init_hook` aborta explícitamente si no existe `completion_porc` o si ya hay más de un expediente para la misma matrícula. El addon no elimina ni fusiona históricos para corregir duplicados.

En una máquina con el runtime autorizado, la instalación o actualización y las pruebas Odoo deben ejecutarse exclusivamente mediante `docker-compose.local.yml`, usando un overlay que monte este worktree cuando corresponda. Después se debe limpiar la base desechable y restaurar el servicio original. En este ordenador no se ejecutó Docker por instrucción expresa del usuario.

## Pruebas y estado de validación

El addon contiene 55 métodos `TransactionCase`/`HttpCase` distribuidos en:

- `tests/test_tfm_convocatorias.py`: cortes, activación, cron, unicidad, concurrencia y asignación.
- `tests/test_tfm_deliveries.py`: ventanas, formatos, límites, versionado, propiedad, inmutabilidad, portal y rutas legacy.
- `tests/test_tfm_elearning.py`: categorías, filtrado, URL directa, QWeb y membresías.

La validación independiente del 7 de septiembre de 2026 aprobó los checks estáticos de AST Python, XML, ACL, manifest, imports, dependencias, estructura de tests, estilo, helpers puros, contratos funcionales/de seguridad, targets de herencia y alcance Git.

Limitaciones de la evidencia disponible en esta máquina:

- No se ejecutaron tests de módulo Odoo, integración PostgreSQL ni concurrencia real porque el usuario prohibió abrir o consultar Docker en este ordenador.
- TestSprite MCP no estaba disponible y no se pudo iniciar su destino Odoo local desechable en el puerto 8069; no se abrió túnel ni se subió código.
- Los 55 tests Odoo están validados estructuralmente, pero no se afirma un resultado de runtime ni E2E.

Antes de desplegar a beta o producción se debe repetir la instalación, la actualización, la suite Odoo y el flujo E2E de MyCampus/eLearning en una máquina que sí disponga de `docker-compose.local.yml` y TestSprite.

## Archivos principales

| Archivo | Responsabilidad |
| --- | --- |
| `models/op_student_course.py` | Elegibilidad, activación inmediata, cron y unicidad. |
| `models/app_gradebook_result.py` | Recalcula el progreso y dispara la activación después de cambios de calificación. |
| `models/irg_tfm_convocatoria.py` | Catálogo y validación de ventanas. |
| `models/tesis_model.py` | Convocatoria, propiedad, chatter y conciliación eLearning. |
| `models/irg_tfm_entrega.py` | Subida, formatos, ventanas, versiones, adjuntos y excepciones. |
| `models/slide_slide.py` | Restricción efectiva por convocatoria. |
| `models/slide_channel_partner.py` | Membresías con procedencia segura. |
| `controllers/portal.py` | MyCampus, descarga, control directo de slides y neutralización legacy. |
| `views/tfm_portal_templates.xml` | Tarjeta, página e historial de entregas. |
| `views/slide_tfm_views.xml` | Configuración de convocatorias en categorías eLearning. |
| `views/tfm_slide_templates.xml` | Ocultación QWeb combinada con lote y prácticas. |

## Referencias

- [Micro-spec](../../micro-specs/2026-09-04-irg-tfm-convocatorias.md)
- [Plan y controles de implementación](../../../missions/irg-tfm-convocatorias/plan.md)
- [Verificación de la misión](../../../missions/irg-tfm-convocatorias/verification.json)
