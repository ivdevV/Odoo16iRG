# Changelog - 2026-10-22 - Caso oral eLearning

## Cambios realizados

* Nuevo módulo `addons-extra/extrairg/irg_oral_case` (16.0.1.0.0).
* Un slide artículo puede marcarse como caso oral y apuntar a un survey sin cambiar de tipo, para que el HTML siga viéndose igual, también en pantalla completa con `isep_slide_article_custom`.
* `POST /irg/oral_case/submit` (usuario autenticado y CSRF) sube el webm y la autoevaluación. El partner sale de la sesión. Odoo crea o reutiliza el `survey.user_input` y lo reenvía a n8n con la cabecera `X-IRG-Key`.
* `GET /irg/oral_case/status` hace de proxy y solo responde al alumno dueño del job.
* `GET /irg/oral_case/bootstrap` da al HTML del slide el token CSRF, los límites y las rutas. No da la clave ni la URL de n8n.
* La URL y la clave se leen de `ir.config_parameter` o de `IRG_ORAL_CASE_N8N_SUBMIT_URL`, `IRG_ORAL_CASE_N8N_STATUS_URL` y `IRG_ORAL_CASE_API_KEY`.
* El docente con grupo Faculty confirma la nota oficial en `app.gradebook.result`. La IA solo rellena `score_ia`, `resumen_ia` y `error_ai`.
* Cron de retención de vídeo con guarda. Por defecto no guarda copia y no borra nada.

## Pendiente de decisión

* Proveedor de IA (está en el flujo de n8n).
* Días de retención y si Odoo guarda copia del vídeo.
* Texto de consentimiento según el RGPD.

## Validación

* Sintaxis Python y XML del módulo, en esta VM.
* Los tests de Odoo no se han ejecutado aquí: no hay Docker ni `docker-compose.local.yml` ni binario de Odoo. El comando queda en el README.
