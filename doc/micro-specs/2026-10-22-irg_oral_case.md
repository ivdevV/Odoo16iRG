# irg_oral_case

## 1. Título corto

Caso práctico oral de eLearning con sugerencia de n8n y nota oficial del docente.

## 2. Resumen objetivo

Un módulo extra recibe la grabación webm y la autoevaluación de un slide artículo, crea la participación `survey.user_input` del alumno y la envía a n8n. La IA solo rellena la sugerencia. El docente confirma la nota en la libreta.

## 3. Motivo / justificación

El slide 7858 (canal 278, caso `DA-ORAL-001`) ya graba en el navegador y no sube nada. El HTML vive en `html_embed_code` y, en pantalla completa, `isep_slide_article_custom` lo pega en la página cuando la categoría es `article`. Cambiar el tipo del slide o editar ese módulo rompería el render. La integración va en un módulo `irg_` nuevo, por herencia.

## 4. Alcance exacto

- Módulo nuevo `addons-extra/extrairg/irg_oral_case`.
- Herencia de `slide.slide`, `survey.user_input` y `res.config.settings`.
- Modelo `irg.oral.case.job` y wizard `irg.oral.case.confirm.grade`.
- Controladores HTTP autenticados de subida, estado y bootstrap.
- Vistas de backoffice para el docente y ajustes del sistema.
- Cron de retención con guarda, inactivo en la práctica por configuración.
- No cambia assets de fullscreen, no edita módulos existentes y no escribe la nota oficial salvo la acción del docente.

## 5. Diseño técnico

- Enlace al survey: `slide.slide.oral_case_survey_id`. No se reutiliza `survey_id` ni se cambia `slide_category`, porque `isep_slide_article_custom` solo inyecta `htmlContent` si `category === "article"`.
- Partner: `request.env.user.partner_id`. El `create` del job lo fuerza si el usuario no es superusuario.
- Acceso al slide: fila `slide.channel.partner` de ese partner, o grupo Faculty para el docente.
- CSRF: `csrf=True` en el POST. El bootstrap devuelve el token para el `fetch` del HTML.
- Secreto: `ir.config_parameter` `irg_oral_case.api_key` y, si tiene valor, `IRG_ORAL_CASE_API_KEY`. Cabecera `X-IRG-Key` solo en la llamada servidor a servidor. `allow_redirects=False`.
- Participación previa en estado `in_progress`, sin `result_id`, para no disparar `send_result` de `isep_gradebook`.
- Nota oficial: `action_confirm` comprueba `openeducat_core.group_op_faculty` y crea o actualiza `app.gradebook.result` sin sudo.
- Campos IA: mismos nombres que `dv_slide_channel_custom` (`score_ia`, `resumen_ia`, `error_ai`). Un alumno no puede escribirlos.
- Cron: patrón de `irg_isep_cron_update_guard` más `retention_enabled` y `retention_days`.

## 6. Dependencias

`website_slides`, `website_slides_survey`, `survey`, `isep_gradebook`.

`isep_gradebook` aporta `app.gradebook.result` y arrastra OpenEduCat. No se depende de `dv_slide_channel_custom` para no activar su cron de OpenAI ni sus librerías.

## 7. Backwards-compatibility / migración

Instalar el módulo no cambia slides existentes: `oral_case_enabled` nace en False. No reescribe HTML ni categorías. Los parámetros de secreto y retención van con `noupdate=1` y valores que no envían nada y no borran nada. Si `dv_slide_channel_custom` ya creó las columnas IA, Odoo reutiliza el mismo campo.

## 8. Casos de prueba / criterios de aceptación

- Acceso denegado sin membresía y sin grupo docente.
- `partner_id` del cliente ignorado en job, participación y multipart.
- Consentimiento ausente o ilegible rechazado.
- Vídeo por encima del máximo y duración por encima del máximo rechazados antes de llamar a n8n.
- POST sin CSRF rechazado.
- Estado de un job de otro alumno: no se llama a n8n.
- La clave de prueba no sale en bootstrap, submit, status ni vistas.
- El alumno no crea `app.gradebook.result`. El docente sí, con su nota, y `score_ia` no pisa `scoring_total`.
- Activar el caso no cambia `slide_category` ni el HTML.
- Con la configuración por defecto el cron no borra el adjunto.

## 9. Rollback plan

Desinstalar `irg_oral_case` desde Apps. Los slides siguen como artículos. Las participaciones y las notas ya confirmadas en la libreta se conservan (no las borra el uninstall de este módulo si la libreta sigue instalada). Para apagar solo la integración sin desinstalar: dejar vacías la URL y la clave, y `oral_case_enabled` en False.

No hace falta reinicio manual: Jenkins solo despliega al entrar el código en `Dev_iRG` (beta) o `main` (producción). Esta entrega no mergea.

## 10. Estimación y responsable

Módulo nuevo, controlador, libreta y cron. Responsable de la entrega: agente de la misión `irg-oral-case`. La decisión de proveedor de IA, retención y texto RGPD queda en el usuario.
