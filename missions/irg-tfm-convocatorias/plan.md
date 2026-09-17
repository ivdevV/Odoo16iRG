# Plan de implementación: irg_tfm_convocatorias

## Objetivo y tier

Implementar el micro-spec `doc/micro-specs/2026-09-04-irg-tfm-convocatorias.md` mediante un addon nuevo bajo `addons-extra/extrairg/`. Tier `complex`: cruza modelos académicos, portal, archivos, eLearning, concurrencia y autorización.

## Arquitectura

- `irg.tfm.convocatoria`: catálogo global con código y dos ventanas fechadas.
- `tesis.model`: convocatoria, activación y relación con entregas; unicidad por matrícula.
- `irg.tfm.entrega`: versiones inmutables por etapa `outline`, `partial`, `final` y convocatoria histórica.
- `op.student.course`: servicio idempotente de elegibilidad basado en el campo real calculado `completion_porc`; se llama al crear/modificar la matrícula, al cambiar calificaciones y desde el cron horario.
- `app.gradebook.result`: disparador heredado para reevaluar las matrículas afectadas después de crear, modificar o eliminar una calificación. El cron conserva la recuperación de cambios que eludan el ORM.
- `op.course`: canal TFM configurado por máster.
- `slide.slide`: convocatorias permitidas en categorías y predicado efectivo heredado por contenidos.
- Controladores seguros de MyCampus para consulta/subida/descarga; se sobrescribe expresamente `/campus/course/<int:course_id>/tfm` sin `super()` y todas las rutas legacy se neutralizan por herencia. El manifest depende de `irg_course_portal_tiles` e `isep_tesis_model` para fijar el orden.
- Helpers fail-closed resuelven `res.users → op.student → op.student.course → tesis.model → irg.tfm.entrega`; cero o múltiples estudiantes/matrículas candidatas deniegan acceso.
- Membresías `slide.channel.partner` con enlaces de procedencia por expediente y marca de creación TFM para no retirar membresías ajenas.

## Tareas TDD

### Task 1: dominio, catálogo y activación

- Escribir pruebas RED de parsing de lote, cortes, progreso, curso habilitado, idempotencia y descenso de progreso.
- Crear esqueleto, hooks, modelos de convocatoria, extensiones de curso/matrícula/tesis, cron, ACL y vistas backend.
- Imponer una ficha por matrícula con constraint PostgreSQL, preflight de duplicados, savepoint y captura exclusiva de esa constraint; validar ventanas/convocatoria activa.
- Suprimir el email heredado únicamente en el contexto de creación automática TFM.

### Task 2: entregas y MyCampus

- Escribir pruebas RED de etapas, ventanas inclusivas, versiones, archivo y propiedad.
- Crear `irg.tfm.entrega`, validación de archivo, rutas seguras, página MyCampus y tarjeta condicional. Portal no tiene ACL directas de create/write/unlink sobre tesis, entregas o convocatoria.
- Serializar la subida bloqueando la fila `tesis.model`, releyendo convocatoria/etapa/ventana y asignando versión mediante constraint SQL.
- Las mutaciones usan POST+CSRF. Archivos: bytes crudos <=20 MiB, no vacíos, extensión normalizada y firma real (PDF, OLE DOC o DOCX ZIP con estructura Word); adjuntos privados ligados solo a la entrega.
- Descarga propietaria con nombre seguro, attachment y `nosniff`; `/web/content/<id>` no debe permitir acceso portal ajeno.
- Versiones inmutables para todos: sin write/unlink histórico. La excepción interna crea una versión nueva mediante método restringido, motivo obligatorio y chatter.
- Neutralizar sin `super()` las rutas `/my/tesis_models/new`, `/my/tesis_models2`, accept, decline, detalle, `/web/submit_documenttr`, download, borrar y comment; eliminar tile y contador `/my`.

### Task 3: eLearning y membresías

- Escribir pruebas RED de contenido común/exclusivo, herencia de categoría, acceso directo y altas/bajas/reasignación.
- Añadir etiquetas de convocatoria, predicado servidor, QWeb combinado y gestión idempotente de membresía.
- Resolver exactamente la matrícula cuyo curso configura el canal, heredar la convocatoria efectiva desde categoría/padre y denegar ante ambigüedad. El gate precede a `super().slide_view()`.
- Una membresía activa ajena puede dar visibilidad al canal, pero TFM no la marca, enlaza ni modifica. Solo se reactiva una archivada creada por TFM para el mismo expediente; las archivadas ajenas nunca se reutilizan. Nunca `unlink`; al retirar solo se archiva una fila creada por TFM sin enlaces restantes ni señales ajenas (`admission_id`, `register_id`, `course_id`, `op_subject_id` u otras presentes). El acceso exclusivo depende siempre de la convocatoria vigente, no solo de membership.

### Task 4: integración, revisión, validación y documentación

- Ejecutar suites completas, sintaxis/XML, instalación/actualización con `docker-compose.local.yml` y E2E TestSprite.
- Review de código y validación por agentes independientes.
- Emitir `verification.json`, evidencias, documentación de módulo, changelog y knowledge reutilizable.

## Riesgos y controles

- El progreso real es `op.student.course.completion_porc`, provisto por `isep_student_filter`; el manifest declarará dependencias directas de `isep_student_filter` y `isep_gradebook`, y el hook comprobará el nombre correcto. `irg_portal_student_fix` no se usará como sustituto transitivo.
- `completion_porc` es calculado, no almacenado y no buscable: el cron no lo incluirá en su dominio SQL. Paginará matrículas de cursos TFM y evaluará el umbral en Python, invalidando antes la caché del progreso.
- La activación inmediata se conectará a `app.gradebook.result.create/unlink` y a `write` solo para `scoring_total`, `survey_type` o `gradebook_subject_id`. Derivará únicamente las parejas alumno/curso de las asignaturas anteriores y posteriores afectadas.
- Antes de comprobar el 50 %, el disparador bloqueará en orden las filas `op.student.course` exactas de esas parejas, recalculará explícitamente `final_subject_note`, persistirá el resultado, invalidará `completion_porc` y lo leerá con `sudo()` limitado a esas matrículas. Esto cierra tanto la caché obsoleta como la carrera entre calificaciones concurrentes.
- El `create` de calificación diferirá el disparador durante la normalización interna de `scoring_total` mediante contexto privado y ejecutará una sola reevaluación al terminar.
- Toda ruta con `sudo()` incorporará la cadena completa de propiedad en el dominio antes de recuperar el registro; no se autoriza por `create_uid`, email ni IDs aislados.
- Asignación, retirada, excepción interna y sincronización de memberships verifican `base.group_user` dentro del método de negocio antes de cualquier `sudo()`.
- El bloqueo de eLearning ocurrirá antes de llamar al controlador padre para impedir efectos como `action_set_viewed()`.
- Los archivos se validarán por extensión, firma/formato real, MIME coherente, tamaño y contenido tanto en UI como en servidor.
- Las operaciones de membresía solo reutilizarán filas archivadas creadas por TFM para el mismo expediente y respetarán la unicidad activa existente.
- Asignación, retirada y subida bloquean el expediente y releen estado para evitar carreras.
- Convocatorias y entregas históricas usan `ondelete='restrict'`; retirar o reasignar nunca borra documentos ni snapshots.

## Publicación

No se hará commit, push ni PR sin autorización independiente y explícita.

## Corrección de instalación QWeb (beta)

- Reproducir el `ParseError` de `course_slides_list_hide_tfm_content` contra la estructura real de `website_slides.course_slides_list_slide` de Odoo 16.
- Sustituir el selector inexistente sobre `div.o_wslides_slides_list_slide` por el nodo raíz real `li` cuyo `t-attf-class` contiene esa clase.
- Mantener el `t-if` en el contenedor completo para que un contenido restringido no deje iconos, badges ni controles visibles.
- Añadir un contrato estático que aplique el XPath a una réplica mínima del padre oficial y exija una coincidencia única.

## Correcciones de aceptación beta (2026-09-08)

### Objetivo y diagnóstico

Corregir los defectos observados durante la prueba funcional completa sin
alterar el flujo ya validado de activación, Esquema, convocatoria y entregas.
Se mantiene el tier `complex`: la corrección cruza portal, matrícula,
membresías, clonación HomeClass/Online, autorización server-side y vistas.

- La pestaña backend muestra solo `ID` porque el one2many
  `irg_tfm_submission_ids` no declara subvista tree propia.
- El portal y la membresía usan directamente `op.course.irg_tfm_channel_id`;
  por eso una matrícula Online recibe el canal HomeClass configurado.
- `irg_course_convocatorias_v2` decide la redirección mediante admisiones
  activas globales, no mediante la matrícula exacta del expediente TFM. La
  ausencia o ambigüedad de admisión provoca el rebote Online → HomeClass.
- La resolución de convocatoria TFM exige igualdad exacta con el canal
  configurado y no reconoce que el canal Online es clon del HomeClass.
- El bootstrap Online no copia `irg_tfm_convocation_ids`; para clones ya
  creados, la restricción debe heredarse dinámicamente desde el original.
- En la subvista de `Secciones iRG`, `is_category` es readonly sin
  `force_save`; al crear sección y convocatoria en una sola operación el
  servidor puede recibir la convocatoria sin el indicador de categoría.

### Diseño aprobado

1. Añadir una subvista tree explícita de entregas con etapa, versión, archivo,
   comentario, convocatoria, autor y fecha, ordenada de más reciente a más
   antigua. Ocultar para expedientes TFM nuevos la fase y documentos legacy.
2. Cambiar el texto del botón a **Guía y recursos para el TFM** y presentar
   las fechas como `dd/mm/aaaa`.
3. Declarar dependencias directas de `irg_course_convocatorias_v2` y del
   controlador final `irg_online_subject_portal_visibility`, y resolver
   un canal base/effectivo con la matrícula exacta: lotes Online usan el clon
   `irg_online_channel_id`; HomeClass usa el canal base. Si falta el clon, la
   operación falla cerrada y no concede acceso al canal equivocado.
4. Usar el canal efectivo tanto en el enlace del portal como en la membresía.
   Al cambiar lote o canal, la conciliación retira solamente referencias TFM
   antiguas conforme a las reglas de procedencia ya existentes.
5. Resolver autorización eLearning dentro de la familia base/clon mediante la
   cadena cerrada `res.users → un op.student activo → expedientes TFM
   activados de la familia → exactamente una matrícula cuyo canal efectivo
   coincide`. La búsqueda recogerá todos los candidatos antes de filtrar; no
   usará `limit=2` sobre matrículas/expedientes antes de calcular el canal
   efectivo. Cero o múltiples candidatos, lote PRS/desconocido, familia rota o
   clon Online ausente deniegan/404. Las rutas de canal y slide neutralizarán
   para familias TFM la decisión global por `op.admission`; solo podrán
   redirigir al miembro efectivo de esa misma familia. El control directo de
   convocatoria sigue ejecutándose antes de cualquier `super().slide_view()`
   que pueda entregar o marcar el material como visto.
6. Copiar `irg_tfm_convocation_ids` solo para categorías en futuros bootstraps
   Online y, para clones existentes, heredar la restricción desde
   `irg_original_slide_id` cuando el clon no tenga configuración local.
   El fallback aceptará solo una categoría original del HomeClass de esa
   familia; una referencia presente pero inconsistente se marca inválida y
   deniega, en lugar de convertirse en contenido común.
7. Heredar la subvista `Secciones iRG` para forzar el guardado de
   `is_category`; mantener el constraint server-side que impide convocatorias
   en materiales reales.
8. Toda mutación de memberships realizada por TFM usará conjuntamente los
   contextos `irg_tfm_membership_sync=True` e `irg_skip_partner_sync=True`, para
   que los hooks de convocatorias V2 no creen, reactiven, archiven ni modifiquen
   una fila hermana. Se probará asignación, retirada y reasignación con una
   admisión Online ajena presente.
9. Heredar `slide.channel.write/unlink` para capturar y reconciliar de forma
   idempotente los expedientes afectados al reemplazar, desvincular o borrar
   `irg_online_channel_id`/`irg_homeclass_channel_id`. La conciliación se hace
   después de obtener el nuevo destino y solo retira referencias con procedencia
   TFM; nunca hace `unlink` ni muta memberships ajenas. Cambiar estos enlaces
   queda restringido server-side a usuarios internos.

### TDD y verificación

- RED/GREEN ORM para selección HomeClass/Online, enlace de portal, membresía
  efectiva, autorización por familia, fallback de restricciones clonadas y
  bootstrap futuro.
- RED/GREEN de rutas de canal y slide para destino correcto y denegación ante
  ambigüedad, lote desconocido o clon ausente; la prueba no confiará en una
  membership como autorización de contenido exclusivo.
- RED/GREEN de lifecycle de familia y de aislamiento de hooks V2, comprobando
  que no quedan memberships TFM obsoletas y que las filas ajenas no cambian.
- RED/GREEN de vistas para columnas del historial, ocultación legacy,
  `force_save`, texto del botón y fechas legibles.
- Review y validación independientes. Por instrucción expresa del usuario no
  se ejecutará Docker en este ordenador; los tests Odoo/PostgreSQL/E2E se
  registrarán como `skipped` con justificación y se ejecutarán los contratos
  estáticos, AST/XML, compilación y comprobaciones Git disponibles.

### Publicación

Esta autorización permite implementar, no hacer commit ni push. Ambas acciones
requieren autorizaciones posteriores, separadas y explícitas.
