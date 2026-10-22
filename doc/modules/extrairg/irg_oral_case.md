# irg_oral_case

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** Instituto Raimon Gaja
**Depende de:** `website_slides`, `website_slides_survey`, `survey`, `isep_gradebook`

El detalle de rutas, campos del POST y códigos de error está en el `README.md` del módulo. Esta ficha es la documentación de `doc/modules/`.

## Qué hace

Conecta un slide artículo de eLearning con el webhook de n8n que sugiere una calificación de un caso oral, y con la confirmación del docente en la libreta.

El alumno graba en el navegador. Odoo comprueba sesión, matrícula, consentimiento, tamaño y duración, crea o reutiliza su `survey.user_input` y reenvía el webm. n8n escribe `score_ia`, `resumen_ia` y `error_ai`. Esos campos ya existían en `dv_slide_channel_custom`; este módulo los declara con el mismo nombre técnico y no depende de ese addon, para no arrastrar su cron de OpenAI.

La nota oficial es `app.gradebook.result.scoring_total`. Solo la escribe el wizard cuando el usuario tiene `openeducat_core.group_op_faculty` y marca la confirmación. No se copia `score_ia`. No se rellena `survey.user_input.result_id`, porque `isep_gradebook` al escribir la participación copiaría `scoring_percentage` encima de la nota si ese enlace estuviera puesto.

## Por qué el slide sigue siendo artículo

`isep_slide_article_custom` pega `htmlContent` en pantalla completa solo si `category === "article"`, y lo hace en la página, sin iframe. `slide.slide.survey_id` de `website_slides_survey` pertenece al flujo de certificación. Un Many2one nuevo, `oral_case_survey_id`, deja el HTML y el fullscreen como están.

## Seguridad

- Rutas con `auth='user'`. El POST lleva CSRF.
- El partner es el de la sesión. El `create` del job lo fuerza para quien no es superusuario ni Settings.
- La clave `X-IRG-Key` y las URL salen de `ir.config_parameter` o de `IRG_ORAL_CASE_API_KEY`, `IRG_ORAL_CASE_N8N_SUBMIT_URL` y `IRG_ORAL_CASE_N8N_STATUS_URL`. No van en el HTML.
- El proxy de estado filtra por el partner de la sesión.

## Retención

El cron diario no borra nada mientras `retention_enabled` sea falso o `retention_days` sea 0, ni si hay módulos en `to install`, `to upgrade` o `to remove`. Esos valores son el defecto. Guardar copia del vídeo en Odoo también nace desactivado. La política queda pendiente de decisión.

## Pendiente de decisión

Proveedor de IA (vive en n8n), días de retención y si se guarda copia, y el texto de consentimiento según el RGPD. El módulo solo exige que el POST traiga una fecha.
