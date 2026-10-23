# Plan — Widget de caso oral por clips (`irg_oral_case` 16.0.2.1.0)

## Clasificación

- Misión: `full`
- Tier: `complex`
- Motivo: más de cinco archivos de producto, asset frontend, controlador HTTP, validación de ficheros subidos, migración de datos de tramos, cron que llama a n8n y cambio de comportamiento visible para la alumna. La subida de MP4 y la migración fuerzan revisión de seguridad antes de implementar.
- Capacidad: Grok 4.7 en este runtime. No hay selector de modelo.
- E2E TestSprite: obligatorio. El diff toca vistas XML, CSS/JS de `web.assets_frontend` y el controlador HTTP. `projectPath` será solo `addons-extra/extrairg/irg_oral_case`. Si el MCP o el runtime local no llegan a estar disponibles, el check queda `skipped` con la causa exacta y `verification.json` no se declara `passed`.

## Conflicto de política resuelto

La skill de Odoo pide no editar módulos ya existentes. El encargo nombra `addons-extra/extrairg/irg_oral_case`, ya fusionado en `Dev_iRG` (PR #54, versión 16.0.2.0.0), y pide subirlo a 16.0.2.1.0. Se modifica solo ese módulo. No se tocan `isep_content_interactive`, `isep_slide_article_custom`, `isep_gradebook` ni el core. La skill cede ante el alcance explícito del usuario.

## Conocimiento consultado

- `AGENTS.md`, `.agents/skills/odoo16_developer/SKILL.md`, `.agents/workflows/odoo16_codebase_knowledge.md`
- `.agents/knowledge/odoo_development_modding/artifacts/irg_oral_case.md`
- `missions/irg-oral-case-clips/plan.md` y el módulo en `Dev_iRG`
- `isep_content_interactive/static/src/js/slides_course_player.js`: la vista normal mete `html_embed_code` en un iframe `srcdoc` con `sandbox` que incluye `allow-same-origin` y `allow="microphone; camera"`. El documento del iframe no carga `web.assets_frontend`.
- `isep_slide_article_custom`: en `?fullscreen=1`, si el slide es `article`, pega el HTML en la página. Ahí el `MutationObserver` del asset sí ve `.o_irg_oral_case`.
- Especificación de UI: `notas_widget.md`, `propuestas_guion_consignas.md`, `qa_marca.md` y `slide_7858_rediseno.html` (scope `.irg-dao1c`, el div del widget va en `.c-widget-slot`).

## Alcance

Solo `irg_oral_case`, más la documentación de esta misión y un changelog fechado en la raíz.

1. El widget arranca en la vista normal del slide y en pantalla completa.
2. El clip de Vimeo (y un `<video>` https que no sea Vimeo) se muestra a 16:9 y tiene un botón «Reproducir». Si el navegador deja hacer `play()`, se usa.
3. Si Vimeo falla o no llega `ended` en el plazo, la alumna puede seguir («Responder ya») con un texto claro.
4. Tras la toma solo quedan «Usar esta respuesta y seguir» y «Repetir respuesta». Hay indicador «Grabando». Repetir no vuelve a poner el clip.
5. El servidor acepta `video/webm` y `video/mp4`, comprobando tipo, extensión, tamaño y firma del contenedor. El contrato n8n se documenta si el multipart deja de ser solo webm.
6. `irg.oral.case.segment` separa el texto que ve la alumna de la consigna que n8n recibe en `prompt`. Migración compatible: los tramos ya existentes siguen enseñando y enviando el mismo texto.
7. No se muestra una duración del clip de la paciente que no haya dicho el reproductor. El «1:30» actual es el máximo de la respuesta y se etiqueta como tal.
8. Al consultar el estado, y con un cron acotado, `state` acompaña a `n8n_status` (`done` o `error` cuando el remoto lo dice). `accepted` no se queda fijo si n8n ya terminó.
9. Textos en español, colores del kit (primario `#074A86`, hover `#063D72`, secundario blanco con borde `#074A86`), foco celeste `#39B4E7` de 3 px, `aria-live`, botones de al menos 44 px.

Fuera de alcance: editar el flujo de n8n, el HTML del slide 7858, otros módulos, la decisión legal del consentimiento, la política de conservación, fusionar o desplegar.

## Garantías que no se tocan

- Campos de sistema del job solo con `env.su`.
- La nota final solo la escribe `openeducat_core.group_op_faculty`.
- `score_ia` no se copia a la libreta ni se muestra a la alumna.
- `oral_case_keep_video` y `irg_oral_case.store_video_copy` siguen en falso por defecto.
- El cron de retención no borra si la política está apagada o hay un módulo en instalación o actualización.
- El modo `single` sigue sin enviar `mode` ni `clips_json`.

## Diseño

### 1. Arranque dentro del iframe `srcdoc`

El asset sigue en `web.assets_frontend` y no se inyecta un `<script>` en el HTML del slide. El observer del documento padre, al ver un iframe, espera a `load` y, si `contentDocument` es accesible (mismo origen), busca `.o_irg_oral_case` ahí y arranca el reproductor en ese documento. En pantalla completa el nodo está en el padre y el camino actual se mantiene. Un `WeakSet` evita el doble arranque. Si el documento del iframe no es accesible, no se fuerza la entrada. El CSS del módulo se enlaza en el `<head>` de ese documento (`/irg_oral_case/static/src/css/oral_case_player.css`), porque el bundle del padre no aplica dentro del iframe. `getUserMedia` y `MediaRecorder` se piden en la ventana del documento donde está el widget, que es la que tiene `allow="microphone; camera"`.

### 2. Vídeo 16:9, reproducir y salida

El clip va en un contenedor con la proporción 16:9 (truco de `padding-bottom: 56.25%`, válido en Safari). Encima, un botón «Reproducir». Al pulsarlo se llama a `play()` del player de Vimeo o del `<video>`. También se intenta `play()` al estar listo; si el navegador lo rechaza, el botón sigue visible. El iframe de Vimeo solo se crea si el host parseado es exactamente `vimeo.com` o `player.vimeo.com`, y se conserva el parámetro `h`. No se concatena HTML.

Salida: «Responder ya» aparece si el player emite error, si la API de Vimeo no llega a cargarse, o si, una vez empezada la reproducción, pasa la duración informada por el player más un margen (o 90 s si el player no dice duración) sin evento `ended`. El texto es: «El vídeo no se ha podido cargar. Puedes leer lo que dice Marta y responder igualmente.» cuando hubo error de carga, y un texto equivalente de tiempo agotado cuando el vídeo llegó a reproducirse pero no terminó. No se muestra al abrir el tramo, para no invitar a saltarse el clip.

La duración que se pinta («El vídeo dura 0:53») sale de `getDuration()` o de `loadedmetadata`. Si no llega, no se pinta ninguna cifra. No se añade un campo de duración del clip de la paciente: un valor guardado a mano sería otra cifra que puede no coincidir con el vídeo.

### 3. Flujo de pantallas

Orden en modo `clips`: inicio, consentimiento (casilla obligatoria, texto provisional), aviso de permiso y clic que llama a `getUserMedia`, prueba de cámara y nivel de voz, vídeo del tramo, consigna, grabación, revisión, resumen, envío, resultado. El modo `single` usa el mismo lenguaje visual con un solo paso y sin clip si no hay URL.

Tras pulsar grabar, el único botón de acción es «Terminar respuesta», con el texto «Grabando» y «Quedan M:SS» (`role="timer"`, `aria-live="off"`). El aviso de voz se limita al inicio, a los 15 s finales (una vez) y al cierre. A los 90 s (o al máximo del tramo) para sola y se guarda la toma.

En la revisión no se vuelven a pintar Grabar ni Parar. «Repetir respuesta» pide confirmación y vuelve a la consigna, sin relanzar el clip. «Volver a ver el vídeo» solo existe en la pantalla de consigna. Menos de 10 s avisa y deja elegir. Si el nivel de audio fue casi nulo durante toda la toma, se avisa y se desactiva «Usar esta respuesta».

Los blobs se conservan en memoria hasta un HTTP 202. Un fallo de red o de n8n ofrece «Reintentar envío» sin regrabar. `beforeunload` pide confirmación del navegador mientras haya tomas sin enviar. La alumna no ve `score_ia`.

### 4. MP4

`_read_webm` pasa a aceptar:

| Declarado | Extensión | Firma |
| --- | --- | --- |
| `video/webm` | `.webm` | EBML `1A 45 DF A3` |
| `video/mp4` | `.mp4` | bytes 4–8 = `ftyp` |
| vacío o `application/octet-stream` | `.webm` o `.mp4` | la firma que corresponda a la extensión |

Cualquier otra combinación es `invalid_video_type`, antes de llamar a n8n. El tamaño se sigue cortando por `max_video_bytes` y por el techo de 200 MiB de la suma. El nombre que se reenvía lo pone el servidor (`clip-N.webm` o `clip-N.mp4`, `oral-case.webm` o `oral-case.mp4`), no el del navegador. El adjunto, si el caso conserva vídeo, guarda ese mimetype. `attachment_is_case_video` acepta `video/webm` y `video/mp4`. La ruta de media responde con ese `Content-Type`, `nosniff` y `inline`, y sigue exigiendo el mismo modelo, id y que no sea público.

El navegador elige `video/webm` si `MediaRecorder.isTypeSupported` lo dice y, si no, `video/mp4`. El `Blob` se envía con ese tipo.

Contrato n8n: el multipart puede llevar `video/webm` o `video/mp4`. No se añaden campos. Se documenta en `doc/n8n_contract.md`. El modo `single` tampoco añade campos; solo admite el segundo tipo.

### 5. Texto de la alumna y consigna de la IA

| Campo | Quién lo ve | Qué se hace con él |
| --- | --- | --- |
| `prompt` (ya existe) | Docente, en el backoffice | Sigue siendo el `prompt` de `clips_json`. No cambia de nombre ni de origen. |
| `student_text` (nuevo) | Alumna | Texto de la consigna en el widget. |
| `student_quote` (nuevo, opcional) | Alumna | Frase citada, si el docente la rellena. Si está vacía, no se inventa. |
| `transcript` (nuevo, opcional) | Alumna, bajo «Leer lo que dice…» | No se envía a n8n. |

`bootstrap` no incluye `prompt`. Incluye `student_text` y, si está vacío, el valor de `prompt`, para que un tramo antiguo siga teniendo texto. Si `student_text` está relleno, el navegador no recibe la consigna de la IA.

Migración `migrations/16.0.2.1.0/post-migrate.py`: `UPDATE` que copia `prompt` a `student_text` solo donde `student_text` está vacío. No borra ni reescribe un texto ya distinto. Tras la migración, lo que ve la alumna y lo que recibe n8n coinciden con el `prompt` de hoy. El docente puede acortar `student_text` y ampliar `prompt` después, sin que el módulo reescriba los guiones (siguen pendientes de revisión clínica).

En el clip de la entrega se guarda `student_text_snapshot` además de `prompt_snapshot`. Lo escribe solo el sistema al crear. No entra en el JSON de n8n.

### 6. Estado del job

Selección nueva: `done` («Propuesta lista»). No sustituye a la nota oficial.

Al guardar la respuesta de estado de n8n (la consulta de la alumna y el cron):

| `n8n_status` remoto | `state` |
| --- | --- |
| `queued`, `processing`, `accepted` | `accepted` |
| `done`, `completed`, `scored` | `done` |
| `error`, `failed`, `failure` | `error` |

`n8n_status` guarda el texto remoto, recortado. `official_score` y la libreta no se tocan. La sugerencia sigue el camino actual (`score_ia`, `resumen_ia`, tramos).

Cron `_cron_refresh_n8n_status` en `irg.oral.case.job`, cada 5 minutos, usuario root, método privado. Sale sin hacer nada si hay módulos en `to install`, `to upgrade` o `to remove`, o si falta la URL o la clave. Como mucho 20 jobs en `accepted` con `n8n_job_id`, creados en los últimos 7 días, los menos recientemente escritos primero. Un fallo de red no pasa el job a `error`. No se registra la clave ni el cuerpo remoto.

## Seguridad (propuesta para el asesor)

- La migración solo copia un texto a una columna nueva vacía. No borra grabaciones ni notas.
- El MP4 se valida en el servidor (tipo, extensión, tamaño, `ftyp`). No se ejecuta. Se sirve autenticado, con `nosniff`, y solo si el adjunto es el de esa entrega.
- La consigna de la IA no viaja al navegador cuando hay texto de alumna.
- El cron usa el mismo canal servidor→n8n que ya existe. No abre una ruta nueva. No escribe la nota final.
- El iframe solo se lee si es del mismo origen. No se relajan las reglas del otro módulo.
- Siguen en pie CSRF, partner de la sesión, matrícula, campos de sistema y retención apagada.

## Pruebas

1. Node, sobre funciones puras (tipo de grabación, mensajes, duración mostrada, botones de cada pantalla, URL de Vimeo) y sobre el fuente del player (sin `innerHTML`, con observer, iframe y «Responder ya»). Primero en rojo.
2. `TransactionCase` / `HttpCase` del módulo, n8n mockeado: MP4 aceptado y webm mal etiquetado rechazado; `clips_json.prompt` sigue siendo el del segmento aunque `student_text` sea otro; `bootstrap` no devuelve ese `prompt`; la migración copia solo si `student_text` está vacío; `fetch_status` con `done` deja `state=done` y no toca `official_score`; el cron refresca sin nota de libreta; un MP4 guardado se sirve con `video/mp4` y un adjunto ajeno sigue en 404.
3. Runtime: `docker compose --env-file .cursor/runtime/compose.env -f docker-compose.local.yml` contra una base desechable. En esta VM no está el runtime al abrir la misión; se intenta materializar el de `cursor/cloud-agent-odoo-runtime-9bea` sin commitearlo (está fuera del diff). Si no arranca, el check queda con la causa exacta.
4. E2E TestSprite después, y solo si el resto pasó, contra `127.0.0.1:8069` y una base desechable. Prohibido beta y producción.

Al terminar se borra la base desechable. No se apunta el compose de despliegue a este trabajo.

## Documentación

README, `doc/n8n_contract.md`, changelog `CHANGELOG_2026-10-23_irg_oral_case_widget.md` y una nota corta en la knowledge de `irg_oral_case` (iframe `srcdoc`, `prompt` frente a `student_text`, MP4).

## Publicación autorizada

Commit y push de `cursor/oral-case-widget-729d`. Una PR en borrador contra `Dev_iRG`. No se fusiona. No se hace push a `Dev_iRG`, `main` ni a otras ramas que despliegan. La PR debe decir que, tras fusionar, hay que actualizar el módulo (`-u irg_oral_case`): Jenkins no ejecuta `-u` en `Dev_iRG`, y sin eso no corren la migración ni los assets nuevos.
