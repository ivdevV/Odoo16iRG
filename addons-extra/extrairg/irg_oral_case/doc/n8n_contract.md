# Contrato con n8n

Odoo llama a n8n. Este módulo no edita el flujo de n8n. La cabecera es `X-IRG-Key`. La clave no vuelve al navegador.

El modo de un solo vídeo no cambia de forma. El modo por tramos añade campos. La respuesta 202 que Odoo espera es la misma en los dos modos.

## Petición, un solo vídeo

`POST` multipart. No van `mode` ni `clips_json`.

| Campo | Origen |
| --- | --- |
| `video` | Fichero `video/webm` o `video/mp4` |
| `case_id` | Código del slide |
| `slide_id` | Id del slide |
| `partner_id` | Partner de la sesión |
| `autoevaluacion_json` | JSON del alumno, ya validado |
| `consent_date` | Fecha de consentimiento |
| `duracion_seg` | Si el alumno la envió |

## Petición, tramos

Los mismos campos de identidad, más:

| Campo | Origen |
| --- | --- |
| `mode` | `clips` |
| `case_title` | Nombre del slide |
| `duracion_seg` | Suma de las duraciones de los tramos |
| `clips_json` | Lista construida en el servidor |
| `clip_1`, `clip_2`, … | Ficheros `clip-N.webm` (`video/webm`) o `clip-N.mp4` (`video/mp4`). El nombre y el tipo los fija Odoo tras comprobar la firma del contenedor. |

Ejemplo de `clips_json`:

```json
[
  {
    "index": 1,
    "segment_id": 15,
    "name": "Apertura",
    "prompt": "Saluda y pregunta el motivo de consulta.",
    "clip_url": "https://player.vimeo.com/video/123",
    "max_seconds": 90,
    "duration_seconds": 40
  }
]
```

`prompt` y `clip_url` son los del segmento en Odoo. Un prompt enviado por el navegador no se reenvía.

`prompt` sigue siendo la consigna que usa la IA. El texto que ve la alumna (`student_text`) no entra en este JSON. En los tramos que ya existían, la migración copia `prompt` a `student_text` y no cambia el `prompt` que se envía aquí. `duration_seconds` es la duración de la respuesta de la alumna, no la del vídeo de la paciente.

El fichero puede ser WebM (firma EBML) o MP4 (caja `ftyp`). No se añaden campos al multipart por ese cambio. Safari y el iPad suelen grabar MP4.

## Respuesta del submit

HTTP 202:

```json
{
  "ok": true,
  "job_id": "job-n8n-1",
  "status": "processing"
}
```

Odoo publica `queued` si ese `status` es `queued`, `processing` o `accepted`. Guarda el valor crudo en `n8n_status`.

Al consultar el estado, Odoo vuelve a guardar `n8n_status` y alinea `state`: `queued`, `processing` o `accepted` dejan la entrega en `accepted`; `done`, `completed` o `scored` la pasan a `done`; `error`, `failed` o `failure` la pasan a `error`. Un cron hace esa misma consulta para entregas `accepted` de los últimos 7 días. Ni la consulta ni el cron escriben la nota final.

## Respuesta de estado

`GET` con `job_id`. HTTP 200. Odoo copia a la participación, y a cada tramo por `index`, solo `score_ia` y `resumen_ia`. Ignora `official_score` y no reasigna adjuntos.

```json
{
  "status": "done",
  "score_ia": 7.5,
  "resumen_ia": "Propuesta global",
  "tramos": [
    {"index": 1, "score_ia": 8, "resumen_ia": "Ve el síntoma"}
  ]
}
```
