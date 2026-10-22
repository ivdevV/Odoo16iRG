# Caso oral en un slide artículo

## Decisión

El caso oral no cambia `slide.slide.slide_category` ni usa `survey_id` de `website_slides_survey`.

`isep_slide_article_custom` solo inyecta el HTML en pantalla completa cuando `category === "article"`, y lo pega en la página sin iframe. Pasar el slide a certificación deja de cumplir esa condición y el HTML deja de verse igual. El enlace al survey es `oral_case_survey_id` en el propio módulo `irg_oral_case`.

## Nota oficial y sugerencia

`score_ia`, `resumen_ia` y `error_ai` están definidos en `dv_slide_channel_custom` y se vuelven a declarar en `irg_oral_case` con el mismo nombre técnico. La nota de la libreta no se escribe al actualizarlos.

`isep_gradebook` en `survey.user_input.write` copia `scoring_percentage` a `app.gradebook.result.scoring_total` si `result_id` está informado. La confirmación docente de `irg_oral_case` crea el resultado por `survey_user_input_id` y no asigna `result_id`. La participación del caso se deja en `in_progress`: `send_result` solo corre al crear una participación ya `done`.

## Retención

El cron de vídeo sigue el corte de `irg_isep_cron_update_guard` (módulos en `to install`, `to upgrade` o `to remove`) y, además, no borra si `retention_enabled` no está activo o `retention_days` es 0.
