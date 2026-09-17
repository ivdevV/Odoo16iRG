# iRG Exam Second Attempt

## Propósito

Gestiona los segundos intentos de cuestionarios académicos y sincroniza sus resultados puntuables con la libreta de Odoo.

## Regla de sincronización

Las respuestas de tipo `survey` solo se sincronizan con la libreta cuando la encuesta tiene puntuación (`scoring_without_answers` o `scoring_with_answers`). Las encuestas `survey` configuradas como `no_scoring`, como las encuestas de satisfacción, se conservan como respuestas eLearning pero no se convierten en exámenes ni generan enlaces o resultados en la libreta.

Las asignaciones mantienen su comportamiento actual aunque utilicen `no_scoring` como configuración técnica, porque pueden recibir una calificación posterior o mediante IA.

## Archivos relevantes

- `models/survey_user_input.py`: filtro común para sincronización automática, sincronización pendiente y flujo heredado `send_result`.
- `tests/test_survey_gradebook_sync.py`: cobertura de encuestas no puntuables, encuestas puntuables y asignaciones.
- `views/survey_templates.xml`: configuración de reintentos.

## Dependencias

- `isep_survey`
- `isep_gradebook`

## Validación

Ejecutar en el runtime local Odoo definido por el repositorio:

```bash
docker compose -f docker-compose.local.yml run --rm odoo_local \
  odoo --stop-after-init --test-enable \
  --test-tags /irg_sync_test -i irg_exam_second_attempt
```

La validación debe comprobar que una encuesta `survey` + `no_scoring` no crea `app.gradebook.result`, mientras que una encuesta puntuable y una asignación sí conservan la sincronización.

## Rollback

Revertir el commit de la versión `16.0.1.0.1` y actualizar el módulo en el entorno autorizado. No se incluyen migraciones de datos ni limpieza histórica automática.

## Changelog

### 16.0.1.0.1

- Evita que encuestas `survey` sin puntuación se envíen a la libreta como exámenes con nota cero.
- Mantiene la sincronización de exámenes puntuables y asignaciones.
- Añade pruebas de regresión para los tres escenarios.
