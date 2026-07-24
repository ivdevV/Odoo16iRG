# Registro de Ejecución: Sincronización y Preservación de Calificaciones en Libretas

## Estado de la Misión
- **Nivel de Misión**: `complex`
- **Fase Actual**: Validación y Documentación Completadas (`passed`)

## Diario de Ejecución

### [Fecha: 2026-07-24] - Preservación Total de Notas Directas al Asignar Plantillas
1. **Identificación de la Causa Raíz**:
   - Al colocar o cambiar la plantilla (`app.gradebook`), se activaba el recompute de `compute_point_average` y `compute_final_subject_note`.
   - Cuando las notas (ej. 8.75) habían sido colocadas directamente sobre la asignatura (`app.gradebook.subject`) por automatizaciones sin crear ítems internos en `gradebook_result_ids`, al ser `gradebook_result_ids` una lista vacía (`len = 0`), los campos `point_average_assignment`, `point_average_exam` y `final_subject_note` se reseteaban automáticamente a `0.00`.
2. **Solución Aplicada**:
   - `compute_point_average` (`irg_gradebook_partial_averages`): Preserva `rec.point_average_*` si no hay resultados en `gradebook_result_ids` en lugar de asignarle 0.0.
   - `compute_final_subject_note` (`irg_gradebook_exam_as_final`): Mantiene `rec.final_subject_note` o los promedios parciales existentes cuando no hay líneas de exámenes registrados en `gradebook_result_ids`.
   - `compute_data_show` (`irg_gradebook_auto_close`): Marca como visible la columna/sección de evaluación si `point_average_* > 0`.
3. **Validación**:
   - Creado test unitario `test_direct_subject_grades_preserved_on_template_set`.
   - Pruebas ejecutadas en Docker local pasando con **100% de éxito (10 pasadas, 0 fallos, 0 errores)**.
