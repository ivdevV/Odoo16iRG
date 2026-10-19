# IRG Student Oficialidad Documents — Design

## Objective

Recibir desde la aplicación Next.js de oficialidad
([ivdevV/oficialidad-app](https://github.com/ivdevV/oficialidad-app)) la
documentación Unimarconi de cada alumno y mostrarla en la pestaña **Detalle
Oficialidad** del expediente (`op.student`), con resumen de completitud y
distinción nacional/internacional, replicando el patrón de becas.

## Scope

Entra en este corte:

- módulo `irg_student_oficialidad_documents` (modelo, catálogo, resumen, UI);
- módulo `irg_student_oficialidad_webhook` (endpoint inbound Bearer + JSON);
- herencia de la página `official_detail` ya existente en
  `isep_control_escolar`;
- descarga de archivos desde el listado del backoffice;
- tests Odoo del servicio y del resumen;
- documentación de módulo y misión `full`.

Queda fuera:

- portal de subida en Campus Odoo;
- pull hacia Google Sheets o la API de lectura de la app;
- cambios en `irg_admission_oficialidad_webhook` (outbound Odoo→n8n);
- cambios en el repo Next.js, salvo descubrimiento de incompatibilidad de
  contrato;
- lógica de negocio de `annex_9` / `certificate_type` (se conservan tal cual).

## Reference: scholarship pattern

Espejo funcional de:

| Beca | Oficialidad |
| --- | --- |
| `irg_student_scholarship_documents` | `irg_student_oficialidad_documents` |
| `irg_student_scholarship_webhook` | `irg_student_oficialidad_webhook` |
| `POST /irg/scholarship/webhook/document` | `POST /irg/oficialidad/webhook/document` |
| pestaña **Beca** | pestaña **Detalle Oficialidad** |

## Architecture

```
oficialidad-app (Next.js)
  POST /irg/oficialidad/webhook/document
    Authorization: Bearer <token>
    JSON por documento
        ↓
irg.oficialidad.webhook.service
  valida token, payload, archivo, tipo, student_type
  resuelve partner/student por email
  crea/actualiza irg.oficialidad.document
  escribe irg_oficialidad_student_type en partner
        ↓
op.student form → page official_detail
  annex_9 (existente)
  resumen derivado + aviso mismatch VAT
  listado descargable de documentos
```

Dependencias:

- `irg_student_oficialidad_documents`: `openeducat_core`, `isep_control_escolar`
- `irg_student_oficialidad_webhook`: `irg_student_oficialidad_documents`

## Student type (nacional / internacional)

La app envía `student_type` (`nacional` | `internacional`) y el listado de
documentos varía según ese valor. Odoo **confía en la app** y persiste el valor
en el partner.

Además calcula un hint a partir del `vat` del contacto (opción A acordada):

- formato DNI/NIE español → hint `nacional`;
- `vat` presente pero no DNI/NIE → hint `internacional`;
- sin `vat` → hint `unknown`.

Si el hint es conocido y distinto de `student_type`, se activa
`irg_oficialidad_type_mismatch` y la UI muestra un aviso. **No se rechaza** el
webhook ni se sobreescribe el tipo enviado por la app.

## Document type catalogue

Modelo `irg.oficialidad.document.type` (XML `noupdate`):

| `key` | Ámbito | Nombre |
| --- | --- | --- |
| `titulo-universitario` | nacional | Título universitario |
| `certificado-notas` | nacional | Certificado oficial de notas |
| `documento-identificativo-nacional` | nacional | DNI / documento identificativo |
| `titulo-universitario-apostillado` | internacional | Título universitario apostillado |
| `apostilla-certificado-notas` | internacional | Apostilla del certificado oficial de notas |
| `pasaporte` | internacional | Pasaporte |
| `matricula-unimarconi` | ambos | Matrícula Unimarconi cumplimentada |

Cada tipo tiene `key`, `name`, `student_type_scope` (`nacional` /
`internacional` / `both`) y `active`.

## Data model

### `irg.oficialidad.document`

- `partner_id` (required, index, cascade)
- `document_type_id` → `irg.oficialidad.document.type` (required)
- `name`, `filename`, `file` (Binary, attachment=True, required)
- `note`, `state` (`submitted` / `accepted` / `observed`, default `submitted`)
- orden: `create_date desc, id desc`

Idempotencia webhook: mismo `partner_id` + `document_type_id` → actualizar
archivo/metadatos (`action=updated`); si no existe → crear (`action=created`).

### Partner / student fields

En `res.partner` (y related en `op.student` donde corresponda):

- `irg_oficialidad_student_type` — Selection `nacional` / `internacional`
- `irg_oficialidad_document_ids` — One2many
- `irg_oficialidad_expected_count` — computed (4 si hay tipo; 0 si no)
- `irg_oficialidad_received_count` — computed (tipos esperados con al menos un doc)
- `irg_oficialidad_last_received_at` — computed
- `irg_oficialidad_completeness` — Char computed con formato `X/4` (p. ej. `3/4`);
  vacío si aún no hay `student_type`
- `irg_oficialidad_is_complete` — Boolean computed (`received == expected` y
  `expected > 0`)
- `irg_oficialidad_vat_hint` — computed `nacional` / `internacional` / `unknown`
- `irg_oficialidad_type_mismatch` — Boolean computed

Checklist: modelo auxiliar computado o líneas readonly generadas a partir de los
tipos esperados para el `student_type` actual; cada línea muestra tipo,
recibido sí/no y estado del documento si existe. No es un One2many editable
independiente del catálogo.

## UI — Detalle Oficialidad

Heredar `isep_control_escolar.op_student_form_inh` (xpath a
`page[@name='official_detail']`), sin eliminar el bloque actual:

1. Grupo existente: `annex_9`, `certificate_type`
2. Resumen:
   - tipo de alumno (readonly desde partner)
   - banner/aviso si `irg_oficialidad_type_mismatch`
   - completitud `X/4` y última recepción
   - checklist de los 4 tipos esperados
3. Listado `irg_oficialidad_document_ids` en tree/form:
   - fecha, tipo, nombre, `file` con `filename` (descarga), estado, nota

Vista equivalente en `res.partner` solo si aporta paridad operativa con becas;
prioridad v1: expediente `op.student`.

Sin portal de alumno en Odoo en v1.

## Webhook contract

`POST /irg/oficialidad/webhook/document`

Headers:

```http
Content-Type: application/json
Authorization: Bearer <token>
```

Token: parámetro de sistema `irg_student_oficialidad_webhook.token` (clave XML
vacía, `noupdate`).

Payload (por documento; contrato de la app):

```json
{
  "email": "alumno@example.com",
  "filename": "titulo_apostillado.pdf",
  "document_name": "Titulo universitario apostillado",
  "document_type_key": "titulo-universitario-apostillado",
  "document_content_base64": "JVBERi0xLjQK...",
  "student_type": "internacional",
  "student_type_name": "Alumno internacional",
  "note": "Solicitud de oficialidad de Ana Perez. Tipo de alumno: Alumno internacional."
}
```

Campos obligatorios: `email`, `filename`, `document_content_base64`,
`document_type_key`, `student_type`.

Validaciones:

- token Bearer con `hmac.compare_digest`;
- JSON objeto;
- `student_type` ∈ {`nacional`, `internacional`};
- `document_type_key` existe y es compatible con `student_type` (scope `both` o
  igual al tipo);
- resolución de partner/student por email (misma semántica que becas:
  `partner_not_found`, `ambiguous_email`);
- base64, extensión (`.pdf`, `.jpg`, `.jpeg`, `.png`, `.doc`, `.docx`), tamaño
  máximo 10 MB, archivo no vacío.

Éxito:

```json
{
  "ok": true,
  "action": "created",
  "document_id": 123,
  "partner_id": 456,
  "student_id": 789
}
```

Errores principales (alineados a lo que ya interpreta la app + extras):

| Código | HTTP |
| --- | --- |
| `missing_token` / `invalid_token` / `webhook_token_not_configured` | 401 |
| `invalid_json` / `missing_required_field` / `invalid_student_type` / `invalid_base64` / `empty_file` / `invalid_file_extension` | 400 |
| `file_too_large` | 413 |
| `partner_not_found` / `document_type_not_found` | 404 |
| `ambiguous_email` / `ambiguous_document_type` / `document_type_student_type_mismatch` | 409 |

Al aceptar un documento válido se escribe `irg_oficialidad_student_type` en el
partner con el valor del payload.

## Security

- Ruta `auth='none'`, CSRF desactivado (servidor-servidor).
- Token obligatorio antes de cualquier lectura/escritura con `sudo`.
- Token no se registra en logs ni mensajes de error.
- Controles de UI no sustituyen la validación del servicio.
- Security Advisor obligatorio antes de implementar (auth pública + secreto).

## Testing

Suite Odoo (`TransactionCase` / HTTP tests según patrón becas):

- auth token ausente, inválido, no configurado;
- email inexistente y ambiguo;
- `student_type` ausente/inválido;
- `document_type_key` desconocido e incompatible con `student_type`;
- create + update idempotente por partner + tipo;
- persistencia de `student_type` y resumen `X/4` / última recepción;
- hint VAT DNI/NIE y `type_mismatch` sin bloquear el webhook;
- límites de archivo (extensión, vacío, tamaño, base64).

E2E TestSprite: obligatorio (diff toca vistas XML del expediente). Runtime:
`docker-compose.local.yml`, `projectPath` = directorio del módulo, nunca la raíz
del repo.

## Mission classification

- Clase: `full` (feature nueva, comportamiento de producto, cross-module).
- Tier: `complex` (>5 archivos, webhook + seguridad + UI + catálogo).
- Jev intake en la sesión de diseño: `skipped` (`http_error`); clasificación
  por política `AGENTS.md`.
- Security Advisor: sí, antes de Implementación.

## Acceptance criteria

1. Con token válido, la app puede enviar los 4 documentos de un alumno nacional
   o internacional y quedan en el expediente bajo **Detalle Oficialidad**.
2. El listado permite descargar cada archivo.
3. Se muestra el tipo de alumno y la completitud `X/4` según el tipo.
4. Si el `vat` sugiere otro tipo, hay aviso visible y el webhook no falla.
5. Reenviar el mismo `document_type_key` actualiza el documento (`updated`).
6. `annex_9` / `certificate_type` siguen funcionando.
7. Tests Odoo en GREEN y check `e2e_testsprite` en PASS (el plan declara
   disparo E2E porque el diff toca vistas del expediente).

## Open follow-ups (explicitly deferred)

- Ajustar la app si en el futuro Odoo debe ser fuente de verdad del tipo
  (hoy la app decide y Odoo solo avisa).
- Portal Campus para consulta/subida.
- Unificar o enlazar con el flujo outbound de admisiones a n8n.
