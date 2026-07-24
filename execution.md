# Registro de Ejecución: Sincronización y Preservación de Calificaciones en Libretas

## Estado de la Misión
- **Nivel de Misión**: `complex`
- **Fase Actual**: Validación y Documentación Completadas (`passed`)

## Diario de Ejecución

### [Fecha: 2026-07-24] - Preservación de Notas sin Línea de Plantilla
1. **Problema Detectado**: Al asignar o aplicar una plantilla de calificaciones (`app.gradebook`), las evaluaciones (`app.gradebook.result`) creadas directamente o por automatización sin una línea correspondiente en `gradebook_template_ids` se ocultaban o se ponían a 0 en el cálculo del promedio.
2. **Solución Implementada**:
   - `compute_data_show` en `irg_gradebook_auto_close`: Mantiene `show_* = True` siempre que `gradebook_result_ids` contenga evaluaciones de ese tipo (`(student_types & line_types) | types_with_results`).
   - `compute_point_average` en `irg_gradebook_partial_averages`: Procesa `gradebook_result_ids` independientemente de si existe línea en la plantilla y calcula la nota promedio.
   - `state_to_done` en `irg_nlex_grade_exemption`: Solo exige cantidades específicas cuando la plantilla tenga configurada una cantidad positiva (`qty > 0`).
3. **Pruebas**: Ejecutadas pruebas unitarias `TestGradebookPartialAverages` en Docker local (0 fallos, 0 errores).

### [Fecha: 2026-07-22] - Sincronización de Cuestionarios
- Implementada la transferencia automática y masiva de `survey` y `cert` a `app.gradebook.result`.
