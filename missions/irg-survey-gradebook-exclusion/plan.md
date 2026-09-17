# Plan — excluir encuestas sin calificación de la libreta

## Tier y alcance

- Tier: `standard` (bugfix localizado en un módulo IRG, con prueba y documentación; no cambia vistas ni despliegue).
- Módulo: `addons-extra/extrairg/irg_exam_second_attempt`.
- Entorno de validación: Odoo local mediante `docker-compose.local.yml` y base de pruebas desechable.
- Entorno de producción: no se modifica en esta misión. La corrección individual de Teresa ya fue aplicada separadamente mediante Odoo Producción.

## Objetivo

Evitar que una respuesta de tipo `survey` configurada con `scoring_type=no_scoring` se sincronice como un resultado de examen en la libreta académica, manteniendo la sincronización de exámenes puntuables y de asignaciones que usan deliberadamente `no_scoring` como configuración técnica.

## Causa confirmada

`irg_exam_second_attempt` incluye respuestas `survey` en el flujo de sincronización y convierte todo tipo distinto de `assignment` en un resultado `exam`. La respuesta de satisfacción de Teresa era `survey` + `no_scoring`, por lo que podía entrar en la libreta con nota cero.

## Diseño técnico

1. Añadir en `models/survey_user_input.py` un predicado interno para reconocer únicamente `survey` + `no_scoring` como encuesta no académicamente puntuable.
2. Aplicar el predicado en:
   - sincronización automática al completar una respuesta;
   - cálculo del conjunto de intentos del mismo cuestionario;
   - sincronización pendiente masiva;
   - `send_result`, para cubrir el flujo heredado de `isep_gradebook`.
3. No excluir asignaciones con `no_scoring`, porque las asignaciones pueden recibir puntuación posterior/IA y deben conservar su flujo actual.
4. Mantener exámenes puntuables aunque el campo relacionado `survey_type` esté almacenado como `survey`, siempre que su `scoring_type` no sea `no_scoring`.
5. Incrementar la versión de parche del módulo y documentar el cambio.

## Archivos previstos

- Modificar `addons-extra/extrairg/irg_exam_second_attempt/models/survey_user_input.py`.
- Modificar `addons-extra/extrairg/irg_exam_second_attempt/tests/test_survey_gradebook_sync.py`.
- Modificar `addons-extra/extrairg/irg_exam_second_attempt/__manifest__.py`.
- Crear/actualizar `doc/modules/extrairg/irg_exam_second_attempt.md`.
- Crear evidencia y logs concisos en `missions/irg-survey-gradebook-exclusion/`.

No se tocarán módulos nativos, `addons_uisep`, archivos de credenciales ni los cambios no relacionados que ya existen en el checkout.

## Criterios de aceptación

- Una respuesta `survey` con `scoring_type=no_scoring` completada no crea ni enlaza un resultado de libreta.
- La acción de sincronización pendiente omite esas respuestas.
- Un examen puntuable (`scoring_without_answers` o `scoring_with_answers`) continúa generando/actualizando su resultado.
- Una asignación con `no_scoring` no queda bloqueada por esta exclusión.
- La prueba específica pasa en rojo antes del cambio y en verde después.
- La suite de pruebas del módulo pasa sin nuevas regresiones.
- La revisión independiente no encuentra errores de seguridad ni de lógica.
- `verification.json` queda en estado `passed` únicamente con evidencia real.

## Riesgos y límites

- No se hará limpieza masiva de respuestas históricas desde el código.
- No se cambiarán notas, estados de libretas ni encuestas existentes en Producción durante esta misión.
- Si el runtime local no está disponible, se registrará el bloqueo y no se presentará una validación fabricada.
- El commit y push a `origin/Dev_iRG` están autorizados para desarrollo; no se hará despliegue automático a Producción.

## Secuencia y responsables

1. Orquestación: plan y control de alcance.
2. Implementación: prueba RED, cambio mínimo y prueba GREEN.
3. Revisión: agente independiente sobre el diff.
4. Validación: tests, lint/sintaxis y verificación de artefactos.
5. Documentación: módulo, changelog y misión.
6. Publicación autorizada: commit y push únicamente a `origin/Dev_iRG` (desarrollo); Producción se mantiene fuera y se actualiza manualmente.
