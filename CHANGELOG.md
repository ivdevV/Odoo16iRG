# CHANGELOG - Sincronización de Cuestionarios y Certificaciones a Libretas

## [2026-07-22] - Corrección de Transferencia a Libretas (`survey.user_input` -> `app.gradebook.result`)

### Añadido
- **Sincronización Ampliada**: Se extendió `_irg_sync_exam_gradebook_result` en `irg_exam_second_attempt` para transferir automáticamente a las libretas de calificaciones los intentos completados (`state == 'done'`) de tipos `survey` y `cert` (además de `exam` y `assignment`).
- **Acción de Regularización Retroactiva**: Implementación del método `action_sync_pending_survey_gradebooks` en `survey.user_input` para procesar de forma masiva los 662+ intentos históricos pendientes que carecen de `result_id`.
- **Suite de Pruebas Unitarias**: Añadido `test_survey_gradebook_sync.py` para validar la transferencia en caliente al pasar a estado `done` y la regularización en lote.

### Corregido
- **Bug de Asignación de Modelos en `get_gradebook`**: Corregida la asignación errónea de `op.subject` a `gradebook_subject_id` en `fix_send_result.py` utilizando `channel_partner_id.search_gradebook_subject()`.
- **Excepción de Método Inexistente**: Eliminada la llamada a `search_subject()` en `fix_send_result.py` que provocaba `AttributeError`.
- **Vistas XML de `isep_gradebook`**: Actualizada la visibilidad de la pestaña y del botón 'Enviar a Libreta' en `survey_user_input.xml` para soportar evaluaciones de tipo `survey` y `cert`.
