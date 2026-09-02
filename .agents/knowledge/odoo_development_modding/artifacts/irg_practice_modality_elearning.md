# irg_practice_modality_elearning

## Contexto

La modalidad de prácticas vive en `practice.center.type` (solicitud) y debe filtrar secciones del canal eLearning **por matrícula**, no por modalidad académica (`irg_content_modality`). `practice.request.course_id` es `op.student.course`.

## Patrón

Dos addons nuevos, herencia solamente:

- A persiste `op.student.course.irg_practice_center_type_id` y sincroniza desde la última solicitud en `approved`/`progress`/`end`.
- B añade `slide.slide.irg_required_practice_type` (Selection, vacío = común) y bloquea en el GET, igual que `irg_batch_slide_restrictions`.

Resolución curso↔canal: `op_subject_ids.course_id` ∪ `op.course.subject_ids` ∪ `op.course.slide_channel_ids`. No hay `course_id` fiable en `slide.channel`.

## Gotchas

- Al sobrescribir `_onchange_parent_slide_apply_limitations` hay que **volver a poner** `@api.onchange('parent_slide_id', 'inherit_limitations_from_parent')`. Sin el decorador Odoo deja de registrar el onchange del padre y se pierde la copia de lote/fecha/categoría.
- El bloqueo de visibilidad debe ir **antes** de `super().slide_view()`: el padre llama a `action_set_viewed()` y entregaría el documento.
- QWeb que oculta secciones debe heredar las plantillas de lote ya combinadas y unir condiciones con `and`; no reescribir solo la de prácticas.
- Un hijo dentro de una sección etiquetada queda restringido aunque su campo esté vacío (`_irg_effective_practice_type` mira categoría y padre). El flag `inherit_limitations_from_parent` solo copia el valor al hijo.
- `op.subject.course_id` y `op.course.subject_ids` no son inversos. Hace falta unir ambas vías.
- Contexto `irg_skip_parent_propagation`: los overrides de `_apply_parent_limitations` deben respetarlo.
