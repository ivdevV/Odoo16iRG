# CHANGELOG - Sincronización y Preservación de Calificaciones en Libretas

## [2026-07-24] - Preservación Total de Notas Directas al Asignar Plantillas

### Corregido
- **Preservación de Notas Almacenadas Directamente (`compute_point_average`)**: Corregido `compute_point_average` en `irg_gradebook_partial_averages` para que, en caso de no haber registros en `gradebook_result_ids`, mantenga los valores almacenados previas en la asignatura (`rec.point_average_assignment`, `rec.point_average_exam`, etc.) en lugar de forzarlos a 0.00 al recalcularse cuando se asigna o cambia una plantilla (`app.gradebook`).
- **Preservación de Nota Final (`compute_final_subject_note`)**: Ajustado `compute_final_subject_note` en `irg_gradebook_exam_as_final` para conservar `final_subject_note` existente o calcular el promedio de promedios parciales cuando la asignatura no tenga líneas en `gradebook_result_ids`.
- **Visibilidad Mejorada por Promedios Directos (`compute_data_show`)**: Actualizado `compute_data_show` en `irg_gradebook_auto_close` para considerar como visibles (`show_* = True`) los tipos de evaluación cuyo promedio almacenado sea mayor a cero (`point_average_* > 0`).

---

## [2026-07-24] - Preservación de Notas sin Línea Interna de Plantilla

### Añadido
- **Visibilidad Dinámica de Evaluaciones (`compute_data_show`)**: Actualizado `compute_data_show` en `irg_gradebook_auto_close` para mantener visible la sección y los campos de promedio (`show_exam`, `show_assignment`, etc.) siempre que la asignatura contenga evaluaciones reales registradas (`gradebook_result_ids`), aunque la plantilla asignada carezca de una línea interna (`gradebook_template_ids`) para ese tipo de evaluación.
- **Cálculo de Promedios por Resultados Reales (`compute_point_average`)**: Ajustado `compute_point_average` en `irg_gradebook_partial_averages` para calcular el promedio aritmético de cualquier tipo de evaluación existente sin reiniciarlo a 0 cuando no exista línea de plantilla o cuando no coincida la cantidad configurada.
- **Validación Flexibilizada en Finalización (`state_to_done`)**: Adaptado `state_to_done` en `irg_nlex_grade_exemption` para exigir el conteo exacto de evaluaciones únicamente cuando la plantilla defina explícitamente una cantidad mayor que cero (`qty > 0`).

---

## [2026-07-22] - Corrección de Transferencia a Libretas (`survey.user_input` -> `app.gradebook.result`)

### Añadido
- **Sincronización Ampliada**: Se extendió `_irg_sync_exam_gradebook_result` en `irg_exam_second_attempt` para transferir automáticamente a las libretas de calificaciones los intentos completados (`state == 'done'`) de tipos `survey` y `cert` (además de `exam` y `assignment`).
- **Acción de Regularización Retroactiva**: Implementación del método `action_sync_pending_survey_gradebooks` en `survey.user_input` para procesar de forma masiva los intentos históricos pendientes que carecen de `result_id`.
- **Suite de Pruebas Unitarias**: Añadido `test_survey_gradebook_sync.py` para validar la transferencia en caliente al pasar a estado `done` y la regularización en lote.
