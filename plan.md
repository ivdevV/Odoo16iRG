# Plan: Transferencia de Cuestionarios y Certificaciones a Libretas de Calificaciones

## Alcance y Clasificación
- **Nivel de Misión**: `complex` (Cambios multi-módulo en `irg_exam_second_attempt`, `isep_gradebook`, `get_gradebook`, flujo de datos académicos, retrocompatibilidad y pruebas unitarias).
- **Capacidad Requerida**: Compleja (Razonamiento de arquitectura Odoo, ORM, multi-módulo y pruebas).

## Criterios de Aceptación
1. **Sincronización al Finalizar**: Cualquier intento de encuesta/evaluación (`survey.user_input`) con respuestas calificadas que pase a estado `done` (`survey_type` en `exam`, `assignment`, `survey`, `cert`) debe crear o actualizar el registro correspondiente en `app.gradebook.result` y asociarlo a la línea `app.gradebook.subject` del alumno.
2. **Corrección de Bugs en `get_gradebook`**:
   - Eliminar la asignación de `op.subject.id` a `gradebook_subject_id` (que requiere un recordset de `app.gradebook.subject`).
   - Eliminar la llamada al método inexistente `self.search_subject()`.
3. **Escala de Calificación Unificada**: Garantizar que `scoring_total` en `app.gradebook.result` se guarde siempre en escala 0–10 (`scoring_percentage / 10.0`).
4. **Regularización Retroactiva**: Proporcionar un mecanismo seguro (método/script) para procesar los intentos históricos completados (`state == 'done'`) que no tienen `result_id` asignado.
5. **Pruebas Automatizadas**: Incluir tests unitarios en Odoo que comprueben la creación automática de `app.gradebook.result` para encuestas tipo `survey` y `cert` al pasar a estado `done`.

## Matriz de Roles
- **Orquestador**: Planificación, descomposición de fases y gates de calidad.
- **Codificador**: Implementación TDD en los módulos correspondientes.
- **Revisor**: Revisión de código, arquitectura Odoo, ausencia de antipatrones.
- **Validador**: Ejecución independiente de suite de pruebas unitarias y comprobación de `verification.json`.
- **Documentador**: Actualización de changelogs y documentación.
- **Responsable de Entrega**: Comprobación final y autorización explícita antes de commit/push.

## Fases del Ciclo de Vida
1. **Plan**: Creación de `plan.md` y `implementation_plan.md`.
2. **Implementación / TDD**:
   - Redactar tests RED para `survey_type == 'survey'` y `'cert'`.
   - Modificar `irg_exam_second_attempt/models/survey_user_input.py`.
   - Modificar `isep_gradebook/models/survey_user_input.py` y vistas XML.
   - Modificar `get_gradebook/models/fix_send_result.py` y `get_books.py`.
   - Implementar método de regularización retroactiva.
   - Pasar tests a GREEN y refactorizar.
3. **Review de Código**: Inspección de diffs y seguridad.
4. **Validación**: Ejecución de pruebas unitarias con Odoo / PyTest y generación de `verification.json`.
5. **Documentación**: Actualización de `CHANGELOG.md` y registro en `execution.md`.
6. **Publicación Autorizada**: Entrega de resultados al usuario.

## Riesgos y Mitigaciones
- **Riesgo**: Duplicación de resultados en libreta al reprocesar intentos antiguos.
  - *Mitigación*: Usar `search` idempotente buscando por `gradebook_subject_id` + `survey_type` + `survey_user_input_id` antes de crear nuevos `app.gradebook.result`.
- **Riesgo**: Incoherencias en escala 0-10 vs 0-100.
  - *Mitigación*: Normalizar siempre usando `_irg_get_exam_score_for_gradebook()` que aplica `answer_score_total` o `round(scoring_percentage / 10.0, 2)`.
