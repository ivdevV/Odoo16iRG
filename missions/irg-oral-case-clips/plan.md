# Plan — Caso clínico por clips (`irg_oral_case`)

## Clasificación

- Misión: `full`
- Tier: `complex`
- Motivo: más de cinco archivos de producto, controlador autenticado, datos de alumnos, adjuntos, libreta de calificaciones, superficie web (vistas, asset y HTTP) y un fallo real de permisos. Seguridad obligatoria antes de implementar.
- Capacidad: Grok 4.7 en este runtime. No hay selector de modelo; no se inventa otro.
- E2E TestSprite: obligatorio. El diff toca vistas XML, un asset frontend y controladores HTTP. `projectPath` será solo `addons-extra/extrairg/irg_oral_case`. Si el MCP o el runtime local no están disponibles, el check queda `skipped` con la causa exacta y el `status` de `verification.json` no será `passed`.

## Conflicto de política resuelto

La skill de Odoo pide no editar módulos ya existentes y crear uno nuevo. El encargo nombra `addons-extra/extrairg/irg_oral_case` y exige compatibilidad con el modo de un solo vídeo. Se modifica solo ese módulo. No se toca `isep_gradebook`, `isep_slide_article_custom`, `website_slides` ni el core. La skill cede ante el alcance explícito del usuario; la regla de no relajar permisos ajenos se mantiene.

## Conocimiento consultado

- `AGENTS.md`, `.agents/skills/odoo16_developer/SKILL.md`, `.agents/workflows/odoo16_codebase_knowledge.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_oral_case.md`
- `missions/irg-oral-case/plan.md` y el módulo ya fusionado en `Dev_iRG` (PR #52)
- `isep_slide_article_custom`: en pantalla completa, si el slide es `article`, pega `slide.htmlContent` con jQuery `.html()`. Esa llamada no ejecuta `<script>`
- `isep_gradebook`: `app.gradebook.result` se nombra `[admisión] asignatura`. Faculty tiene create y write, no unlink. `write` de la libreta solo toca el redondeo si hay `gradebook_subject_id`
- Regla de `website_slides` para `base.group_user`: un slide publicado solo es legible si el canal está publicado o el usuario es el autor. El canal del test no se publica. Por eso el wizard, al leer `slide.oral_case_enabled` como docente, recibe `AccessError`. Es un bug del módulo, no del test

## Alcance

Todo dentro de `irg_oral_case`, más la documentación de la misión y un changelog fechado en la raíz, al estilo de `CHANGELOG_2026-10-22_irg_oral_case.md`.

1. Configuración del caso por slide: modo `single` (defecto) o `clips`, tramos ordenados, clip de escucha opcional y un interruptor por slide para conservar las grabaciones.
2. Una entrega con varias grabaciones, cada una ligada a su tramo, con validación en el servidor. El POST de un solo `video` sigue igual cuando el modo es `single`.
3. Contrato n8n de entrada y de respuesta, con ejemplo JSON, en la documentación del módulo. No se edita n8n.
4. El profesor ve el desglose por tramo. La nota final la pone solo `openeducat_core.group_op_faculty`, desde el formulario y desde la lista, y el wizard se queda como atajo.
5. Reproductor de referencia servido por el módulo. El HTML del slide es un contenedor con el id del slide.
6. Conservar el vídeo es un ajuste del slide, por defecto apagado. En la entrega no hay un selector de adjuntos.
7. Dejar la suite en verde, incluidos los dos fallos de la PR #53 y el `status` público `queued`.
8. Cerrar el agujero de los Many2one editables visto en BETA.

Fuera de alcance: editar el flujo de n8n, decidir la política de retención (sigue pendiente de Iván), validar el texto legal, desplegar BETA o PROD, y fusionar.

## Diseño

### Por qué este diseño

El slide tiene que seguir siendo `article`. El fullscreen pega el HTML sin ejecutar scripts, así que el reproductor no puede vivir dentro del HTML del slide: un asset de `web.assets_frontend` arranca solo si encuentra el contenedor, también cuando el fullscreen lo inyecta después (MutationObserver). No se hereda `slides_course_fullscreen_player` ni se menciona `isep_slide_article_custom`. El test que prohibía la clave `assets` se actualiza a esa regla: el asset propio está permitido; sustituir el fullscreen no.

La nota que edita el profesor es el float `official_score`, con etiqueta «Nota final (profesor)». Los enlaces a la libreta, al adjunto y a la auditoría los escribe solo el superusuario (`env.su`). No autorizan ni un flag de contexto ni `base.group_system`: el cliente puede mandar el contexto en el RPC, y un administrador técnico no es el superusuario. El alta legítimo lo hace el servicio con `sudo()` y un diccionario armado en el servidor, después de capturar el partner de la sesión. El docente escribe la nota; el `sudo()` que guarda el enlace usa un diccionario fijo y el uid del docente capturado antes del `sudo()`. La libreta se crea o se actualiza con el entorno del docente, sin sudo.

### Configuración en el slide

Campos nuevos en `slide.slide`:

| Campo | Uso |
| --- | --- |
| `oral_case_mode` | `single` (defecto) o `clips` |
| `oral_case_keep_video` | Boolean, defecto False. Si está activo, el sistema guarda la copia |
| `oral_case_listen_clip_url` | URL https opcional del clip de escucha del caso |
| `oral_case_segment_ids` | Tramos |

Modelo `irg.oral.case.segment`: `sequence`, `name`, `clip_url`, `prompt`, `max_seconds`, `allow_retry`, `listen_clip_url` opcional. Máximo 20 tramos. Crear o editar exige `check_access_rights('write')` y `check_access_rule('write')` sobre ese `slide_id`. El alumno no tiene ACL. `slide_id` no se reasigna si no hay `env.su`.

Cada URL del modelo se valida con `urlsplit`: esquema `https`, sin userinfo, sin espacios y sin barra invertida. Si no pasa, no se guarda y `bootstrap` responde `invalid_case_config` sin incluirla. El iframe del reproductor solo se usa si el host parseado es exactamente `vimeo.com` o `player.vimeo.com`. El resto de las https van a un `<video>`, nunca a un iframe. El `src` se asigna como propiedad del nodo, no concatenando HTML.

La copia se guarda si `oral_case_keep_video` es verdadero o si el parámetro global `irg_oral_case.store_video_copy` ya estaba activo. El global se conserva para no apagar una instalación que lo hubiera encendido. El interruptor que usa el personal académico es el del slide. Los dos nacen en False: el comportamiento por defecto no cambia. La política sigue pendiente de Iván.

### Entrega y compatibilidad

`irg.oral.case.clip`: tramo, índice, consigna y URL del momento (copiadas en el envío), duración, `score_ia`, `resumen_ia` y el adjunto. El job de un solo vídeo no necesita clips: sigue usando `video_attachment_id`.

Validación del POST, toda en el servidor:

- El partner es el de la sesión. `partner_id` y `case_id` del cliente se ignoran.
- Modo `single`: el contrato actual (`video`, webm, tamaño, duración, consentimiento, autoevaluación). Un `clips_json` en ese modo responde `single_video_expected`.
- Modo `clips`: hacen falta todos los tramos activos, en el orden de `sequence`, índice 1..n, `segment_id` real de ese slide, un fichero `clip_<índice>` webm, duración dentro del tramo y del máximo del sistema, y la suma de bytes dentro del techo duro de 200 MiB. Cada fichero respeta además `max_video_bytes`.
- Si esa alumna ya tiene nota final confirmada en ese slide, `grade_already_confirmed` y no se llama a n8n.
- Antes de la confirmación, un segundo envío sigue creando otro job, como hoy.

`allow_retry` solo lo usa el reproductor para repetir el tramo antes de enviar. El servidor recibe la toma final.

### Contrato n8n

El modo `single` no añade campos. Así el flujo actual no se rompe.

El modo `clips` añade `mode=clips` y `clips_json`, y sustituye el fichero `video` por `clip_1`, `clip_2`, … El JSON lleva el índice, el id del tramo, la consigna, la URL del clip de la paciente y la duración. La respuesta 202 no cambia. Si n8n devuelve `processing`, `accepted` o `queued`, la respuesta pública del submit dice `queued`. El valor crudo queda en `n8n_status`.

El estado que devuelve n8n puede incluir `score_ia`, `resumen_ia` y `tramos` (`index`, `score_ia`, `resumen_ia`). Al consultar el estado, el `sudo()` persiste solo esos dos campos en la participación y, por tramo, solo `score_ia` y `resumen_ia` del clip cuyo índice coincide. No copia la nota final ni reasigna adjunto, job o tramo. La clave se redacta si vuelve en un error. Faculty puede escribir `score_ia` y `resumen_ia` del clip, igual que hoy en la participación, y no el resto.

El ejemplo JSON queda en `addons-extra/extrairg/irg_oral_case/doc/n8n_contract.md` y en el README.

### Nota final

- Etiquetas: `score_ia` → «Nota propuesta por IA»; `official_score` → «Nota final (profesor)». Los nombres técnicos no cambian. El help dice que la nota final es la del cuaderno y que solo la pone el profesor.
- Rango 0 a 10 en `write` y en un constraint. 0 es una nota válida.
- La alumna de la nota es `job.partner_id`. Tiene que coincidir con `user_input.partner_id`, y el slide del job con `user_input.slide_id`. Si no, `AccessError` y no se escribe la libreta.
- La línea existente solo se actualiza en `scoring_total` y `rated_by`, y solo si su `survey_user_input_id` es esa participación. Si tiene asignatura, el `partner_id` de la asignatura tiene que ser el de esa alumna. Si la asignatura es de otra alumna, o tiene partner vacío, `AccessError` y no se toca. Una línea sin asignatura solo se actualiza si además su `channel_partner_id` es la matrícula de esa alumna en ese canal.
- Al crear, `channel_partner_id` es la matrícula de ese partner en ese canal. La asignatura del wizard solo se guarda si su `partner_id` es el de esa alumna. Partner vacío se rechaza. Si el formulario numérico no trae asignatura, la línea nace sin asignatura y queda atada a la participación y a la matrícula.
- La nota de la IA no se copia. No se asigna `user_input.result_id`.
- Se puede cambiar después de confirmada. Cada cambio deja en el chatter quién, cuándo, el valor anterior, el nuevo y el motivo opcional (`official_score_reason`). El cuerpo se escapa.
- El wizard sigue. Llama al mismo método. Sigue exigiendo el checkbox y el grupo Faculty.
- La lista de Casos orales es editable solo en la nota final y el motivo. El resto va `readonly` en la vista y, sobre todo, bloqueado en `write`.

### Campos que solo escribe el sistema

En `create` y en `write`, si no hay `env.su` y el vals trae uno de estos campos, `AccessError` y no se crea ni se modifica nada. En el job: `partner_id`, `slide_id`, `survey_id`, `user_input_id`, `case_code`, `consent_date`, `duration_seconds`, `autoevaluacion_json`, `state`, `n8n_job_id`, `n8n_status`, `last_error`, `video_attachment_id`, `video_stored_at`, `video_purged`, `gradebook_result_id`, `official_confirmed_by`, `official_confirmed_at`. En el clip: adjunto, job, tramo e índice.

El portal y el usuario interno pierden `perm_create` del job. El servicio hace el alta con `sudo()` y un diccionario propio: el partner es el capturado de la sesión antes del `sudo()`, el slide es el que ya pasó el control de acceso y la participación es la de esa pareja partner+slide. No hay ningún método, público o privado, que reciba un id de adjunto o de libreta y lo escriba con `sudo()`. El adjunto lo crea el servicio a partir de los bytes que acaba de leer, y el id que guarda es el que acaba de crear.

ACL del clip: el portal y el usuario interno no tienen acceso. Faculty tiene `perm_create=0` y `perm_unlink=0`, y solo puede escribir `score_ia` y `resumen_ia`. Borrar clips o adjuntos exige `env.su`.

`official_score` y el motivo solo los escribe Faculty, en `write`, con un número finito de 0 a 10 incluido. El resto de campos del job, para quien no es superusuario, dan `AccessError`.

La vista oculta los Many2one técnicos o los deja de solo lectura: el enlace a la línea del cuaderno, quién confirmó y cuándo. No hay desplegable de adjuntos. Si el caso conserva el vídeo, el formulario muestra `<video>` contra la ruta del módulo, con ids enteros y sin iframe. Si no, un aviso de que el vídeo no se guarda. El nombre «Copia del vídeo» desaparece de la participación; queda un indicador de solo lectura «Vídeo guardado».

La ruta de reproducción es `auth=user` y sin CSRF, porque la usa un `<video>`. El id de la URL es el del job o del clip, entero. Se resuelve con el entorno del usuario, de modo que la `ir.rule` aplica; si no es visible, 404. Después se comprueba que el adjunto guardado tenga ese id, `res_model` y `res_id` coincidan, `public` sea falso y el MIME sea `video/webm`. Solo entonces se leen los bytes con `sudo()`. La respuesta fija `Content-Type: video/webm` y `X-Content-Type-Options: nosniff`, y no redirige a `/web/content`. Cualquier otro caso es 404, sin leer otro registro.

El cron solo hace `unlink` del adjunto si cumple esas mismas condiciones de `res_model`, `res_id`, id y MIME. Si el puntero no las cumple, limpia el campo y deja el adjunto donde estaba.

En `survey.user_input`, si el registro es un caso oral (el slide tiene `oral_case_enabled`, leído con sudo solo para decidir la restricción), quien no es `env.su` no puede escribir `partner_id`, `slide_id`, `survey_id` ni `result_id`. No se aplica al resto de encuestas: `isep_gradebook` asigna `result_id` en exámenes normales y un bloqueo global los rompería. El caso oral no asigna `result_id`. Un alta no superusuario de una participación de caso oral solo se admite si el `partner_id` es el de la sesión.

### Bug del wizard

`action_confirm` lee `oral_case_enabled` y `channel_id` con sudo, después de comprobar Faculty y solo sobre la participación que el docente ya puede abrir. No se añade una regla que abra todos los slides a Faculty: el canal sin publicar seguiría oculto en eLearning. No se devuelve el HTML del slide.

### Bug de `assertRaises`

`assertRaises((AccessError, MissingError))` revienta con `TypeError` de `issubclass` en este runtime. El test pasa a un `try/except` que sigue aceptando esas dos excepciones y falla ante cualquier otra o ante la ausencia de error. No se relaja la comprobación.

### Reproductor

Asset `irg_oral_case/static/src/js/oral_case_player.js` y un CSS mínimo. HTML del slide:

```html
<div class="o_irg_oral_case" data-slide-id="SLIDE_ID"></div>
```

El id de caso y los tramos salen de `bootstrap`, no del HTML. El texto de consentimiento lo sirve el servidor, marcado `pending_legal_review`. Pide la cámara una vez, al aceptar. Encadena el clip: `<video>` para cualquier https que no sea Vimeo; iframe solo si el host es exactamente `vimeo.com` o `player.vimeo.com`, conservando la query del hash de privacidad. El iframe se crea por DOM y el `src` es una propiedad. Al terminar, pausa, muestra la consigna, pone en bucle y en silencio el clip de escucha si existe, y graba con `MediaRecorder` hasta el máximo del tramo. Si el tramo permite repetir, se puede regrabar antes de seguir. Al final, un solo `FormData`. Sin base64. Consignas, consentimiento y errores van con `textContent`. jQuery `.html()` del fullscreen no se usa como sanitizador.

### Retención

El cron sigue sin borrar si la política no está activada. Cuando borra, borra también los adjuntos de los clips. Por defecto no guarda y no borra.

## Seguridad (para el asesor, antes de implementar)

- Autenticación de las rutas: `auth=user`. El anónimo va al login.
- Autorización de la nota: Faculty en el servidor. La vista no basta.
- Los Many2one técnicos solo con `env.su`, en `create` y en `write`. El contexto RPC y `base.group_system` no autorizan. El portal no tiene `perm_create` del job.
- No hay un método que reciba un id de adjunto o de libreta y lo persista con `sudo()`. El diccionario del enlace es fijo y el uid del docente se captura antes del `sudo()`.
- La libreta no se escribe con sudo. La línea es la de esa participación y esa alumna. La asignatura del wizard se rechaza si el partner es otra alumna o está vacío.
- La ruta de reproducción resuelve el job con la `ir.rule` del usuario y solo entonces lee bytes, y solo si `res_model`, `res_id`, MIME y `public` cuadran. El cron no borra un adjunto que no cumpla eso.
- En participaciones de caso oral, `partner_id`, `slide_id`, `survey_id` y `result_id` solo los escribe el superusuario. El resto de encuestas no cambia, para no romper `isep_gradebook`.
- URL de tramo solo `https`. No se acepta `javascript:`.
- Techo de tamaño, de duración, de número de tramos y de longitud del JSON.
- La clave de n8n no sale en bootstrap, vistas, estado ni logs.
- El consentimiento es provisional y está marcado pendiente de revisión legal. No se presenta como texto cerrado.
- No hay secretos en el repositorio.

## Criterios de aceptación

1. Un slide en modo `clips` se configura desde el formulario del slide, sin código.
2. El POST de clips rechaza tramos de más o de menos, orden distinto, MIME no webm, duración por encima del tramo, tamaño de más y un segundo envío tras la nota final. No llama a n8n en esos casos.
3. El POST de un solo `video` en modo `single` sigue respondiendo 202 y el multipart hacia n8n no gana campos nuevos obligatorios.
4. Si n8n responde `processing`, el cliente ve `status: queued`.
5. El portal no crea un job con adjunto, libreta o participación ajenos: el `create` sin `env.su` que traiga esos campos recibe `AccessError` y no inserta nada. Faculty, con y sin flag de contexto, no escribe `gradebook_result_id`, `video_attachment_id`, `official_confirmed_by`, `official_confirmed_at` ni `video_stored_at`. La nota numérica de 0 a 10 escribe `scoring_total` y `rated_by` en la línea de esa participación y no modifica una línea ajena. Una asignatura de otra alumna, o con partner vacío, no recibe la nota. 11 y un valor negativo se rechazan. `score_ia` no se copia. Un segundo guardado actualiza la misma línea y deja rastro. `official_confirmed_by` es el docente, no el superusuario del `sudo()`.
6. La ruta de vídeo responde 404 a un adjunto ajeno y a la entrega de otra alumna, y no redirige a `/web/content`. El cron no borra un adjunto cuyo `res_model` no es el del job o del clip: limpia el puntero y deja el fichero.
7. El wizard confirma aunque el canal no esté publicado, sin abrir el HTML del slide a Faculty por una regla nueva.
8. La alumna no escribe la sugerencia ni la nota final. En una participación de caso oral, quien no es superusuario no cambia `partner_id`, `slide_id`, `survey_id` ni `result_id`.
9. Con el interruptor del slide apagado y el global apagado no hay adjunto. Con el del slide encendido, el sistema guarda la copia y el formulario muestra el reproductor o el aviso, nunca un selector de `ir.attachment`.
10. El manifiesto no referencia `isep_slide_article_custom` ni el fullscreen de slides. El asset propio sí está.
11. El README y `doc/n8n_contract.md` traen el contrato y un ejemplo JSON.

## Pruebas

`TransactionCase` y `HttpCase` del módulo, n8n mockeado. Primero los tests nuevos en rojo, luego el mínimo código, luego verde. El runtime de Docker está en la rama `cursor/cloud-agent-odoo-runtime-9bea` y no entra en el diff. Comando de tests contra `docker-compose.local.yml` o el compose de ese runtime, base desechable, módulo `irg_oral_case`. Al terminar se borran usuarios y datos de la base desechable; no se apunta el compose compartido a un worktree.

E2E con TestSprite después de que el resto pase, `projectPath` en el directorio del módulo, puerto local 8069, base desechable, usuario de esa base. Prohibido BETA y PROD.

## Roles

| Fase | Rol |
| --- | --- |
| Plan | Orquestador |
| Security Advisor | Revisión del diseño, antes de código. Veredicto `[YES]` o `[NO]` |
| Implementación / TDD | Codificador |
| Review de código | Subagente distinto del codificador |
| Validación | Subagente que no edita producción y emite `verification.json` |
| Documentación | Documentador |
| PR borrador | Responsable de entrega. Rama `cursor/oral-case-clips-8297` contra `Dev_iRG`. Sin merge y sin deploy |

## Publicación autorizada

Commit y push solo a `cursor/oral-case-clips-8297`. Una PR en borrador contra `Dev_iRG`. Prohibido push a `Dev_iRG` o `main`, merge y cualquier uso de BETA o PROD.

## Pendiente de Iván

Hay que decidir si Odoo conserva las grabaciones y durante cuántos días. El interruptor por slide nace apagado. El texto de consentimiento es provisional y no está validado legalmente.
