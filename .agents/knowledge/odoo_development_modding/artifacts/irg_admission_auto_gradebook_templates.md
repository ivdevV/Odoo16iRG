# Auto gradebook templates on enrollment

## Patrón

Módulo puente posterior a `irg_admission_auto_gradebook` que, tras `super().enroll_student()`,
rellena `app.gradebook.student.gradebook_id` solo si está vacío. Depende de
`irg_gradebook_editable_template` para que el valor escrito sobreviva al recompute
(`gradebook_id or course.gradebook_id`).

## Precedencia

1. Template del curso (compute).
2. Diplomado → xml_id `irg_diploma_gradebook_template_weighting.gradebook_diploma_exam_50_50`.
3. Máster (tipo o nombre inequívoco) → xml_id `...gradebook_master_solo_examen` o nombre `Solo Examen`.
4. Resto → vacío.

## Gotcha de tests

No invocar el enroll real de OpenEduCat/`isep_openeducat_custom` en TransactionCase
ligeros: crea `res.users` sin `login`. Ejercitar `_irg_assign_auto_gradebook_templates`
tras crear la libreta como hace el auto-módulo.
