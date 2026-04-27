# Micro-spec: irg_survey_second_attempt_fix

## 1. Titulo corto
Habilitar segundo intento real en examenes tipo test de eLearning.

## 2. Resumen objetivo
Corregir el flujo de examenes tipo test para que el alumno pueda iniciar un segundo intento en lugar de caer directamente en la pantalla de resultado del primer intento.

## 3. Motivo / justificacion
`isep_survey` fuerza los examenes academicos como surveys con intentos limitados, pero no garantiza que el limite sea de dos intentos. Como no se modifica Odoo nativo ni `isep_survey`, la correccion se implementa en el modulo extra existente `irg_survey_second_attempt_fix` mediante herencia de modelos y hook de actualizacion.

## 4. Alcance exacto
- Modelo heredado: `survey.survey`.
- Modelo heredado existente: `survey.user_input`.
- Hook de instalacion y XML de datos para surveys tipo examen ya existentes.
- Documentacion tecnica del modulo.
- Sin cambios de vistas, controladores, assets ni permisos.

## 5. Diseno tecnico
- Agregar `models/survey.py` con `_inherit = 'survey.survey'`.
- En `create()` y `write()`, cuando `survey_type == 'exam'`, asegurar:
  - `is_attempts_limited = True`.
  - `attempts_limit >= 2`.
- Mantener intacto el comportamiento de `assignment`, que usa puntuacion/manualidad distinta.
- Agregar metodo `irg_fix_exam_attempt_limits()` ejecutado desde XML de datos para que tambien corra en `-u`.
- Agregar `hooks.py` con `post_init_hook` para cubrir instalaciones frescas.
- Conservar la correccion existente de `survey.user_input.scoring_success` para que el resultado mostrado corresponda al intento actual.

## 6. Dependencias
`depends`: `isep_survey`.

## 7. Backwards-compatibility / migracion
La actualizacion automatica solo afecta `survey.survey` con `survey_type = 'exam'`. No toca encuestas generales, asignaciones, certificaciones ni examenes que ya tengan mas de dos intentos configurados.

## 8. Casos de prueba / criterios de aceptacion
1. Al crear un survey tipo `exam`, queda con `is_attempts_limited=True` y `attempts_limit=2` si no se indico un limite mayor.
2. Al cambiar un survey existente a tipo `exam`, queda con limite minimo de dos intentos.
3. Un survey tipo `exam` con `attempts_limit=3` conserva sus tres intentos.
4. El hook corrige examenes existentes con limite menor que dos.
5. En flujo funcional, tras finalizar el primer intento, el alumno puede iniciar un segundo intento nuevo y no se muestra directamente el resultado anterior.

## 9. Rollback plan
Actualizar o desinstalar el modulo segun proceda:

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_survey_second_attempt_fix \
    --stop-after-init --db_host=pgodoo_latest
```

Para revertir manualmente la configuracion academica, ajustar `attempts_limit` desde la vista tecnica del survey/examen afectado.

## 10. Estimacion y responsable
- Estimacion: 1 hora.
- Responsable: iRG / GitHub Copilot.
