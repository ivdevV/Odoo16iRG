# Micro-spec: irg_survey_regrade_attempts

## 1. Titulo
Recalificacion manual de intentos en survey.user_input

## 2. Resumen
Agregar un modulo extra que permita recalificar intentos de encuestas/examenes desde `survey.user_input`, recalculando score y sincronizando la libreta cuando exista `result_id`.

## 3. Motivo / justificacion
En operacion academica es necesario recalificar intentos despues de ajustes en respuestas o puntajes sin depender de crear un nuevo intento.

## 4. Alcance exacto
- Modelo heredado: `survey.user_input`
- Campos nuevos: fecha y usuario de ultima recalificacion
- Vista: boton "Recalificar intento" en formulario de `survey.user_input`
- Sin cambios en modulos existentes

## 5. Diseno tecnico
- Modulo nuevo en `addons-extra/extrairg/irg_survey_regrade_attempts`
- Metodo `action_regrade_attempt`:
  - Ejecuta recalculo de score (`_compute_scoring_values`)
  - Recalcula `answer_score_total` si existe
  - Persiste score para disparar hooks existentes
  - Sincroniza `result_id.scoring_total` con regla de mejor intento

## 6. Dependencias
- `survey`
- `isep_survey`
- `isep_gradebook`

## 7. Backwards-compatibility / migracion
No aplica. Es funcionalidad adicional opt-in por boton.

## 8. Criterios de aceptacion
1. En formulario de `survey.user_input` se muestra boton de recalificar en estados completados.
2. Al recalificar, se actualizan `scoring_total/scoring_percentage` del intento.
3. Si existe `result_id`, se actualiza `scoring_total` en libreta respetando mejor intento.
4. Se registra `x_last_regraded_on` y `x_last_regraded_by`.

## 9. Rollback plan
Desinstalar modulo `irg_survey_regrade_attempts`.

## 10. Estimacion y responsable
- Estimacion: 2-3 horas
- Responsable: Equipo iRG
