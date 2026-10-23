# Caso oral en un slide artículo

## Decisión

El caso oral no cambia `slide.slide.slide_category` ni usa `survey_id` de `website_slides_survey`.

`isep_slide_article_custom` solo inyecta el HTML en pantalla completa cuando `category === "article"`, y lo pega en la página sin iframe. Pasar el slide a certificación deja de cumplir esa condición y el HTML deja de verse igual. El enlace al survey es `oral_case_survey_id` en el propio módulo `irg_oral_case`.

## Nota oficial y sugerencia

`score_ia`, `resumen_ia` y `error_ai` están definidos en `dv_slide_channel_custom` y se vuelven a declarar en `irg_oral_case` con el mismo nombre técnico. La nota de la libreta no se escribe al actualizarlos.

`isep_gradebook` en `survey.user_input.write` copia `scoring_percentage` a `app.gradebook.result.scoring_total` si `result_id` está informado. La confirmación docente de `irg_oral_case` crea el resultado por `survey_user_input_id` y no asigna `result_id`. La participación del caso se deja en `in_progress`: `send_result` solo corre al crear una participación ya `done`.

## Retención

El cron de vídeo sigue el corte de `irg_isep_cron_update_guard` (módulos en `to install`, `to upgrade` o `to remove`) y, además, no borra si `retention_enabled` no está activo o `retention_days` es 0.

## Escritura técnica

Un flag de contexto no autoriza a escribir la línea del cuaderno ni el adjunto: el RPC puede enviarlo. Esas escrituras exigen `env.su`. La nota (`scoring_total`, `rated_by`) la escribe el docente, no el superusuario. El enlace en la entrega, con un diccionario fijo, sí va en sudo y el uid del docente se captura antes.

`survey.user_input.result_id` no se rellena en un caso oral. `isep_gradebook` copia `scoring_percentage` a la línea si ese campo está puesto. El bloqueo de `partner_id`, `slide_id`, `survey_id` y `result_id` vale solo para participaciones de caso oral, para no romper el resto de exámenes.

## Reproductor en un artículo

El fullscreen de artículo pega el HTML y no ejecuta scripts. El reproductor es un asset de `web.assets_frontend` que detecta el nodo con `MutationObserver` y un `WeakSet`. Un atributo de “ya arrancado” se copiaría con el HTML y el clon no arrancaría. El iframe de un clip solo se usa si el host es exactamente `vimeo.com` o `player.vimeo.com`.

`isep_survey.compute_slide_channel_partner` no admite varias participaciones en la misma llamada. Guardar la nota hace flush. El módulo lo ejecuta de una en una, con la misma búsqueda, para que dos participaciones pendientes no aborten el guardado.
