# irg_oral_case

Entrega de un caso práctico oral grabado en un slide de eLearning. Odoo autentica al alumno, crea o reutiliza su `survey.user_input` y reenvía el webm a n8n. La IA solo sugiere. La nota oficial la confirma un docente en `app.gradebook.result`.

El slide sigue siendo un artículo. Este módulo no cambia `slide_category`, no toca `html_embed_code` y no sustituye el JavaScript de `isep_slide_article_custom`. En pantalla completa, si el slide es `article`, ese módulo sigue pegando el HTML en la página.

## Configuración

Ajustes (solo administración) o parámetros del sistema. También vale una variable de entorno si no está vacía; en ese caso gana sobre el parámetro.

| Parámetro | Entorno | Por defecto |
| --- | --- | --- |
| `irg_oral_case.n8n_submit_url` | `IRG_ORAL_CASE_N8N_SUBMIT_URL` | vacío |
| `irg_oral_case.n8n_status_url` | `IRG_ORAL_CASE_N8N_STATUS_URL` | vacío |
| `irg_oral_case.api_key` | `IRG_ORAL_CASE_API_KEY` | vacío |
| `irg_oral_case.max_video_bytes` | — | `52428800` (techo duro 200 MiB) |
| `irg_oral_case.max_duration_seconds` | — | `600` (techo duro 14400) |
| `irg_oral_case.store_video_copy` | — | `False` |
| `irg_oral_case.retention_days` | — | `0` |
| `irg_oral_case.retention_enabled` | — | `False` |

La clave viaja solo en la cabecera `X-IRG-Key` de la llamada de servidor a n8n. No se pinta en el HTML ni se devuelve al navegador.

En el slide (backoffice, sin cambiar el tipo):

- `oral_case_enabled`
- `oral_case_code` (por ejemplo `DA-ORAL-001`)
- `oral_case_survey_id`

El `case_id` que llega a n8n es el del slide. Un `case_id` o `partner_id` enviado por el navegador se ignora. El partner es `request.env.user.partner_id`.

## Rutas

Todas con `auth='user'`. Hay que estar matriculado en el canal del slide (`slide.channel.partner`). Un docente del grupo Faculty también pasa el control de acceso.

### `GET /irg/oral_case/bootstrap?slide_id=<id>`

Respuesta 200:

```json
{
  "ok": true,
  "csrf_token": "<token de la sesión>",
  "slide_id": 7858,
  "case_id": "DA-ORAL-001",
  "max_video_bytes": 52428800,
  "max_duration_seconds": 600,
  "submit_url": "/irg/oral_case/submit",
  "status_url": "/irg/oral_case/status"
}
```

No incluye la clave ni la URL de n8n.

### `POST /irg/oral_case/submit`

`multipart/form-data`. CSRF activo: el campo `csrf_token` es obligatorio. Sin él Odoo responde 400 con el texto `Session expired (invalid CSRF token)`, no el JSON de esta tabla.

| Campo | Obligatorio | Notas |
| --- | --- | --- |
| `csrf_token` | sí | El de `bootstrap` |
| `slide_id` | sí | Entero |
| `video` | sí | Fichero `video/webm` (o `application/octet-stream` con nombre `.webm`) |
| `consent_date` | sí | `YYYY-MM-DD` o ISO `YYYY-MM-DDTHH:MM:SS` |
| `autoevaluacion_json` | sí | String JSON: objeto o lista, máximo 20000 caracteres |
| `duracion_seg` | no | Número ≥ 0. Si viene, no puede pasar del máximo |
| `partner_id` | no | Se ignora |
| `case_id` | no | Se ignora |

Respuesta 202:

```json
{
  "ok": true,
  "job_id": "id-devuelto-por-n8n",
  "status": "queued",
  "status_url": "/irg/oral_case/status?job_id=id-devuelto-por-n8n"
}
```

`status_url` es el proxy de Odoo, no el de n8n.

Odoo reenvía a n8n, en multipart, `video`, `case_id`, `slide_id`, `partner_id` (el de la sesión), `autoevaluacion_json`, `consent_date` y, si vino, `duracion_seg`.

Antes de llamar, crea o reutiliza el `survey.user_input` de ese alumno, ese survey y ese slide, en estado `in_progress`. n8n puede escribir ahí `score_ia`, `resumen_ia` y `error_ai`. Esos campos no son la nota oficial.

### `GET /irg/oral_case/status?job_id=<id>`

Solo el alumno dueño del job. Otro alumno recibe 404 `job_not_found` y Odoo no llama a n8n.

Respuesta 200, solo estos campos:

```json
{
  "job_id": "id-devuelto-por-n8n",
  "status": "done",
  "score_ia": 7.5,
  "duracion_fuera_rango": false,
  "user_input_id": 123,
  "error": null,
  "updated_at": "2026-10-22T12:00:00"
}
```

`user_input_id` es el de Odoo. `score_ia` es la sugerencia, no la nota de la libreta.

## Códigos de error

El cuerpo es `{"ok": false, "error": "<código>"}`. En `n8n_rejected` hay además `errors`, una lista de textos ya redactados.

| HTTP | `error` | Cuándo |
| --- | --- | --- |
| 400 | `missing_slide` | `slide_id` ausente o no numérico |
| 404 | `slide_not_found` | No existe |
| 403 | `slide_forbidden` | Sin matrícula en el canal y sin ser docente |
| 400 | `not_oral_case` | El slide no tiene caso, código y survey |
| 400 | `missing_consent` | Sin `consent_date` |
| 400 | `invalid_consent` | Fecha ilegible |
| 400 | `missing_self_assessment` | Sin `autoevaluacion_json` |
| 400 | `invalid_self_assessment` | No es un objeto o lista JSON, o pasa de 20000 caracteres |
| 400 | `missing_video` | Sin fichero |
| 400 | `empty_video` | Fichero vacío |
| 400 | `video_too_large` | Supera el máximo (y el techo de 200 MiB) |
| 400 | `invalid_video_type` | No es webm |
| 400 | `invalid_duration` | `duracion_seg` no es un número ≥ 0 |
| 400 | `duration_exceeded` | Supera el máximo (y el techo de 14400 s) |
| 400 | `invalid_job_id` | El id de estado no cumple el formato |
| 404 | `job_not_found` | No existe o no es del alumno de la sesión |
| 400 | `n8n_rejected` | n8n respondió 400, o 202 con `ok` falso |
| 502 | `n8n_unavailable` | Red, respuesta inesperada o `job_id` inválido |
| 503 | `n8n_not_configured` | Falta URL o clave |
| 500 | `server_error` | Fallo interno, sin detalle |

Un usuario anónimo no recibe este JSON: `auth='user'` lo manda al login.

## HTML del slide

El HTML actual puede seguir grabando el webm. Para subirlo, desde la misma página (el fullscreen de artículo lo pega sin iframe; si otro módulo lo mete en un iframe `srcdoc` con `allow-same-origin`, el `fetch` same-origin también lleva la cookie):

```javascript
const boot = await fetch('/irg/oral_case/bootstrap?slide_id=' + SLIDE_ID, {
  credentials: 'same-origin',
});
const info = await boot.json();
const body = new FormData();
body.append('csrf_token', info.csrf_token);
body.append('slide_id', String(info.slide_id));
body.append('consent_date', '2026-10-22');
body.append('autoevaluacion_json', JSON.stringify({ preparacion: 4 }));
body.append('duracion_seg', String(seconds));
body.append('video', blob, 'caso.webm');
const sent = await fetch(info.submit_url, {
  method: 'POST',
  body: body,
  credentials: 'same-origin',
});
const accepted = await sent.json();
const status = await fetch(accepted.status_url, { credentials: 'same-origin' });
```

No hace falta, ni se debe, poner la clave en ese script. El texto legal del consentimiento queda pendiente de decisión RGPD: aquí solo se exige que llegue una fecha.

## Nota del docente

En la participación o en Casos orales (menú eLearning) el docente ve `score_ia`, `resumen_ia` y `error_ai`. El botón **Confirmar nota oficial** abre un wizard. Solo `openeducat_core.group_op_faculty` puede ejecutarlo. La nota que escribe es `official_score`; no se copia sola desde `score_ia`. Hace falta marcar la confirmación.

Eso crea o actualiza `app.gradebook.result` (`scoring_total`, `rated_by` el docente, `survey_type` examen o asignación). No se rellena `survey.user_input.result_id`, para que un write posterior de la sugerencia no machaque la nota oficial.

El usuario de Odoo con el que n8n escribe `score_ia`, `resumen_ia` y `error_ai` tiene que ser técnico (`base.group_system`) o docente. Un alumno no puede escribir esos campos. Ese usuario no debe confirmar la libreta: la confirmación es una acción del docente en Odoo.

## Vídeo y retención

Por defecto no se guarda copia en Odoo y el cron no borra nada. El cron diario existe y sale sin tocar adjuntos si hay módulos en instalación o actualización, si `retention_enabled` no está activo o si `retention_days` es 0. Las tres cosas hay que decidirlas antes de activar el borrado. Queda pendiente.

## Pruebas

```bash
docker compose -f docker-compose.local.yml exec -T odoo_local odoo \
  -c /etc/odoo/odoo.conf -d <bd_desechable> -i irg_oral_case \
  --test-enable --test-tags=/irg_oral_case --stop-after-init \
  --http-port=8099 --log-level=test
```

n8n se mockea. No hace falta la clave real.
