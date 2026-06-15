# irg_course_elearning_featured_section

## Contexto

La relacion usada por el portal entre curso academico y asignaturas eLearning es:

- `op.course.subject_ids` contiene las asignaturas academicas.
- `op.subject.slide_channel_id` apunta al canal eLearning de la asignatura.
- `slide.channel.op_subject_ids` es el inverso One2many definido por `isep_elearning_custom`.
- `op.course.slide_channel_ids` se usa para canales complementarios/no curriculares.

## Patron Aplicado

Para configurar un bloque comun a todas las asignaturas de un curso, no se debe duplicar contenido en cada `slide.channel`. Se configura el contenido en `op.course` y `slide.channel` resuelve su curso relacionado mediante `op_subject_ids`, con fallback a `slide_channel_ids` para complementarios.

Para iframes o codigo de insercion, no usar `fields.Html` con editor HTML porque el saneado/editor puede eliminar tags embebidos. Usar un `fields.Text` dedicado y renderizarlo con `Markup` solo para contenido configurado desde backend por usuarios de confianza.

## Gotcha

`slide.channel` no tiene un `course_id` directo fiable en esta instancia. Cualquier feature global por curso debe resolver el curso desde `op.subject` o desde `op.course.slide_channel_ids`.

`isep_elearning_custom` anade la categoria `certification` a `website_slides`, pero no define los contadores `nbr_certification`. Cualquier modulo que dependa de ese stack y cree/cargue canales puede disparar `_compute_slides_statistics` y obtener `KeyError: 'nbr_certification'` si no existen `slide.channel.nbr_certification` y `slide.slide.nbr_certification`.
