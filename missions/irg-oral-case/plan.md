# Plan — irg_oral_case

## Alcance

Módulo nuevo `addons-extra/extrairg/irg_oral_case` que conecta un slide de eLearning de tipo artículo (caso oral grabado en el navegador) con el webhook de n8n que sugiere una calificación, y con la confirmación docente de la nota oficial en `app.gradebook.result`.

La IA solo sugiere (`survey.user_input.score_ia`, `resumen_ia`, `error_ai`). Ningún proceso de este módulo escribe `app.gradebook.result.scoring_total` salvo la acción explícita del docente.

No se modifica `isep_slide_article_custom`, `isep_content_interactive`, `dv_slide_channel_custom` ni el core. El slide sigue siendo `article`: el HTML de `html_embed_code` / `html_content` y el pegado a pantalla completa de `isep_slide_article_custom` no cambian.

## Clasificación

- Misión: `full`
- Tier: `complex`
- Motivo: módulo nuevo con controlador autenticado, secreto de servidor, datos de alumnos, borrado de vídeo, libreta de calificaciones y más de cinco archivos de producto.
- Security Advisor: obligatorio antes de implementar (autenticación, secreto, borrado). Veredicto en `artifacts/security-advisor.txt`.
- E2E TestSprite: el orquestador lo declara obligatorio porque el diff incluye XML en `views/` y controladores HTTP. Si el MCP no está en este runtime, el check queda `skipped` con esa causa; no se rebaja el disparo.

## Capacidad

Runtime de este agente (Grok 4.7). No hay selector de modelo real; no se inventa otro tier de modelo.

## Roles

| Fase | Rol |
| --- | --- |
| Plan | Orquestador |
| Security Advisor (diseño) | Revisión previa, artefacto `[YES]`/`[NO]` |
| Implementación / TDD | Codificador |
| Review de código | Revisor distinto del codificador |
| Validación | Validador |
| Documentación | Documentador |
| PR | Responsable de entrega. Sin merge y sin deploy |

## Conocimiento consultado

- `SPECIFICATIONS.md`, `PROJECT.md`, `AGENTS.md`, `.agents/INSTRUCTIONS.md`, `.agents/skills/odoo16_developer/SKILL.md`
- `.agents/knowledge/odoo_development_modding/artifacts/modding_rules_and_email_analysis.md`
- `doc/micro-specs/biblia-desarrollo-modulos-automatizaciones-irg.md` (cron con guarda, módulo extra, changelog)
- `isep_slide_article_custom`: en pantalla completa, si el slide es `article`, pega `slide.htmlContent` en la página, sin iframe
- `irg_content_interactive_super_fix`: otro fullscreen mete el HTML embebido en un iframe `srcdoc`. Este módulo no toca ninguno de los dos
- `dv_slide_channel_custom`: ya define `score_ia`, `resumen_ia` y `error_ai` en `survey.user_input`. Este módulo los declara otra vez con el mismo nombre técnico para poder instalarse si ese addon no está, y reutiliza la columna si ya está
- `isep_gradebook`: `app.gradebook.result` y `survey.user_input.write` que, si `result_id` está puesto, copia `scoring_percentage` a `scoring_total`. Por eso la confirmación docente no asigna `result_id`
- `irg_isep_cron_update_guard`: la retención sale si hay módulos en `to install` / `to upgrade` / `to remove`

## Diseño

### Enlace slide ↔ survey

No se usa `slide.slide.survey_id` de `website_slides_survey`: ese campo va ligado a contenidos de certificación y cambiar `slide_category` dejaría de cumplir `category === "article"` en `isep_slide_article_custom`, así que el HTML dejaría de pintarse igual en pantalla completa.

Campos nuevos en `slide.slide`, sin tocar la categoría:

- `oral_case_enabled` (Boolean, default False)
- `oral_case_code` (Char, p. ej. `DA-ORAL-001`)
- `oral_case_survey_id` (Many2one `survey.survey`)

El `case_id` que se reenvía a n8n sale del slide, nunca del cliente.

### Participación

Se crea o reutiliza el `survey.user_input` del partner de la sesión, el survey del slide y ese `slide_id`, en estado `in_progress` (no `done`), para que `isep_gradebook.create` no llame a `send_result`. n8n necesita ese registro antes de escribir la sugerencia.

### Controladores (`auth='user'`, CSRF en el POST)

- `GET /irg/oral_case/bootstrap?slide_id=` — token CSRF, límites y rutas propias. Sin clave ni URL de n8n.
- `POST /irg/oral_case/submit` — multipart. Partner = `request.env.user.partner_id`. Comprueba acceso al slide (membresía `slide.channel.partner` del partner de sesión, o grupo docente), consentimiento, tamaño y duración. Reenvía a n8n y devuelve `job_id`.
- `GET /irg/oral_case/status?job_id=` — proxy. Solo el partner dueño del job. La lista blanca de la respuesta no incluye la clave.

La clave `X-IRG-Key` y las URL salen de `ir.config_parameter`, con variable de entorno solo si no está vacía:

| Parámetro | Entorno | Default |
| --- | --- | --- |
| `irg_oral_case.n8n_submit_url` | `IRG_ORAL_CASE_N8N_SUBMIT_URL` | vacío |
| `irg_oral_case.n8n_status_url` | `IRG_ORAL_CASE_N8N_STATUS_URL` | vacío |
| `irg_oral_case.api_key` | `IRG_ORAL_CASE_API_KEY` | vacío |
| `irg_oral_case.max_video_bytes` | — | 52428800, techo duro 200 MiB |
| `irg_oral_case.max_duration_seconds` | — | 600, techo duro 14400 |
| `irg_oral_case.retention_days` | — | 0 |
| `irg_oral_case.retention_enabled` | — | False |
| `irg_oral_case.store_video_copy` | — | False |

### Modelo `irg.oral.case.job`

Relaciona `n8n_job_id`, partner, slide, survey, `user_input`, consentimiento, duración y, si el docente confirma, `gradebook_result_id`. El `create` de un usuario no superusuario fuerza `partner_id` al de la sesión.

### Nota oficial

Wizard `irg.oral.case.confirm.grade`. Solo `openeducat_core.group_op_faculty` ejecuta `action_confirm`. Escribe `app.gradebook.result` con el `official_score` tecleado por el docente y `rated_by` el partner del docente. No copia `score_ia`. No asigna `survey.user_input.result_id`. Exige un checkbox de confirmación.

Grupo `irg_oral_case.group_oral_case_teacher` implicado por el grupo Faculty, para ver sugerencia y jobs. La escritura de la libreta sigue exigiendo Faculty en el servidor.

### Retención

Cron diario `_cron_apply_video_retention`. No borra nada si hay una operación de módulos en curso, si `retention_enabled` no está activo, si `retention_days` es 0, o si no hay adjunto. Por defecto las tres condiciones de borrado están apagadas. Pendiente de decisión del usuario. No se guarda copia del vídeo en Odoo salvo que `store_video_copy` se active.

## Criterios de aceptación

1. El POST autenticado rechaza a quien no es miembro del canal, sin consentimiento, con vídeo o duración por encima del límite, y sin CSRF.
2. Un `partner_id` enviado por el cliente no se usa ni en el job, ni en el `survey.user_input`, ni en el multipart hacia n8n.
3. El GET de estado de un job ajeno no llama a n8n y no devuelve el estado.
4. La clave no aparece en vistas, bootstrap, submit ni status.
5. El alumno no crea `app.gradebook.result`. El docente sí, con la nota que él indica, distinta de `score_ia` cuando así la escribe.
6. Activar el caso oral no cambia `slide_category` ni el HTML del slide.
7. El cron no borra adjuntos con la configuración por defecto.

## Pruebas

`TransactionCase` y `HttpCase` en el módulo, n8n mockeado con `unittest.mock`. Comando canónico de `PROJECT.md` si hay `docker-compose.local.yml`. En esta VM no hay Docker ni ese compose: se registra el intento y la causa.

## E2E

Disparo declarado: sí (vistas XML y controladores HTTP). Ejecución solo con TestSprite contra el Odoo local del puerto 8069 y `projectPath` en el directorio del módulo. Prohibido beta y producción.

## Publicación

- Rama de trabajo: `cursor/irg-oral-case-ed40` (esta ejecución exige ese prefijo; `PROJECT.md` prefiere `feat/<misión>`. Se explica en la PR).
- PR contra `Dev_iRG`. Sin merge.
- Jenkins (`Jenkinsfile`) despliega beta solo en la rama `Dev_iRG` y producción solo en `main`. Esta rama no despliega. No se hace push a `Dev_iRG` ni a `main`.

## Pendiente de decisión del usuario

- Proveedor de IA (lo elige el flujo n8n, no este módulo).
- Retención del vídeo (días y si se guarda copia).
- Texto de consentimiento según el RGPD (lo pondrá el HTML del slide; este módulo solo exige una fecha).
