# CHANGELOG - Sincronización y Preservación de Calificaciones en Libretas

## [2026-07-24] - Módulo irg_hide_portal_servicios (Ocultar Servicios Adicionales en Portal)

### Añadido
- **Módulo `irg_hide_portal_servicios`**: Creado nuevo módulo en `addons-extra/extrairg/irg_hide_portal_servicios` que, al ser activado, oculta la sección de "Servicios adicionales" del portal de clientes (`/my/home`) mediante la sobreescritura limpia del template `isep_openeducat_reports.portal_my_home_servicios_menu`.

### Corregido
- **Prevención de Error JS (`TypeError: Cannot set properties of null`) en `portal.js`**: Añadido placeholder oculto `<span data-placeholder_count="servicios_count" style="display:none !important;"/>` en `irg_hide_portal_servicios` y en `irg_portal_placeholder_safe`. Esto evita que `portal.js` en el cliente lance una excepción `TypeError` al intentar asignar `textContent` cuando el backend devuelve contadores de `servicios_count` pero el elemento visual no está visible en el DOM.
- **Corrección de Validación XML RelaxNG (`AssertionError: Element odoo has extra content: data`)**: Eliminada la etiqueta `<data>` innecesaria dentro de `<odoo>` en `irg_portal_placeholder_safe/views/portal_templates.xml` que provocaba que la validación estricta RelaxNG de Odoo 16 abortase el proceso de instalación de módulos.

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

### Corregido
- **Bug de Asignación de Modelos en `get_gradebook`**: Corregida la asignación errónea de `op.subject` a `gradebook_subject_id` en `fix_send_result.py` utilizando `channel_partner_id.search_gradebook_subject()`.
- **Excepción de Método Inexistente**: Eliminada la llamada a `search_subject()` en `fix_send_result.py` que provocaba `AttributeError`.
- **Vistas XML de `isep_gradebook`**: Actualizada la visibilidad de la pestaña y del botón 'Enviar a Libreta' en `survey_user_input.xml` para soportar evaluaciones de tipo `survey` y `cert`.
