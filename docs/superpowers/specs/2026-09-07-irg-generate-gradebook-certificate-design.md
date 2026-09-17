# Design: `irg_generate_gradebook_certificate`

Date: 2026-09-07
Module: `irg_business_api` (`irg.api.operation`)
Consumer: agente IA (Lisa / MCP) que debe generar el certificado y **pasar el PDF** por su canal (Chat, correo, etc.)

## Problem

La fachada no expone la generación de certificados de notas. Lisa solo tiene lecturas y CRUD cerrado. El PDF se genera hoy por la UI (`irg.certificate.wizard`). Un agente no puede obtener el fichero sin `execute_kw` genérico ni sin publicar el adjunto.

## Goal

Un comando allowlist que:

1. Valida en servidor el payload y el estado de la libreta.
2. Genera el PDF con el flujo oficial del wizard backend.
3. Devuelve metadatos **y** `file_b64` para que el agente reenvíe el PDF.
4. Deja el adjunto privado en Odoo y no envía ni publica nada automáticamente.

## Agent workflow

```text
create irg.api.operation
  operation_code = irg_generate_gradebook_certificate
  environment     = test | beta
  idempotency_key = <clave del agente>
  request_payload = { gradebook_student_id, document_type, certificate_type, signer, ... }
        │
        └─ state=preview  (sin PDF)
              │
create irg_approve_operation { operation_id }
        │
        └─ state=verified
           result_snapshot = {
             certificate_request_id, name, state,
             attachment_id, attachment_name, mimetype,
             checksum, file_b64, public: false
           }
```

El agente verifica `checksum == sha256(b64decode(file_b64))` y pasa `file_b64` por su canal. Odoo no manda el PDF al alumno ni pone `public=True`.

`idempotency_key` es campo de `irg.api.operation`, no clave del JSON. Misma clave + mismo hash reutiliza la operación y no duplica el certificado.

## Payload (`request_payload`)

| Clave | Obligatorio | Valores |
| --- | --- | --- |
| `gradebook_student_id` | sí | id de `app.gradebook.student` |
| `document_type` | sí | `gradebook_partial` \| `gradebook` |
| `certificate_type` | sí | `digital` \| `physical` \| `custom` \| `physical_apostilled` |
| `signer` | sí | `dpto_academico` \| `raimon` (sin default silencioso) |
| `shipping_type` | si físico | `national` \| `international` |
| `custom_description` | no | texto, solo útil con `custom` |
| `custom_options` | no | `language_en` \| `language_fr` \| `specific_subjects` \| `official_seal` |

Claves extra → error. `production` → error (contrato actual).

## Server validation (preview y apply)

- `irg.certificate.wizard` / `irg.certificate.request` instalados; si no, error claro.
- Libreta existente.
- Firmante presente y válido.
- Parcial: libreta abierta permitida.
- Final (`gradebook`): libreta `state == done`.
- Físico / físico apostillado: `shipping_type` obligatorio.
- Apply: si la libreta cambió de estado desde el preview, error.

## Official generation

Apply crea `irg.certificate.wizard` con esos valores y llama `action_generate()`:

- `origin=backend`, `state=done`
- `irg.certificate.request._generate_and_attach_pdf()`
- no factura portal, no plantillas mail, no `_send_digital_notification`

El PDF se recupera del `ir.actions.act_url` (`/web/content/<attachment_id>`), no por un `search` al último registro.

Lectura del binario con `with_context(bin_size=False)`.

## Result (after approve)

```json
{
  "certificate_request_id": 88,
  "name": "CERT/2026/0088",
  "state": "done",
  "attachment_id": 1442778,
  "attachment_name": "Certificado_....pdf",
  "mimetype": "application/pdf",
  "checksum": "<sha256 hex of raw PDF bytes>",
  "file_b64": "<base64 PDF>",
  "public": false
}
```

- `file_b64` se llama así (no `datas`) para no ser recortado por `SECRET_TOKENS`.
- El snapshot puede ser grande; es deliberado: el agente necesita el fichero.
- El adjunto en `ir.attachment` permanece `public=False`.
- Si `public` es verdadero tras generar, apply falla.

## Out of scope

- Diplomas u otros `document_type` del modelo.
- Controlador HTTP nuevo.
- Arreglar Google Chat / ADC (el informe de Chat de una generación UI es ajeno).
- Envío automático al alumno o publicación del adjunto.
- Comando genérico de descarga de cualquier `ir.attachment`.

## Security

- Mismo grupo `irg_business_api.group_irg_business_api_user` y `sudo()` solo tras allowlist + grupo (patrón existente).
- No flags de contexto RPC. `write()`/`unlink()` siguen denegados.
- No dependencia dura de `irg_gradebook_certificates` (igual que `irg_get_gradebook_summary`).

## Knowledge

- `.agents/knowledge/odoo_development_modding/artifacts/irg_business_api_command_facade.md`
- Wizard: `addons-extra/extrairg/irg_gradebook_certificates/wizard/certificate_wizard.py`
- Contrato: `addons-extra/extrairg/irg_business_api/doc/api-contract.md`
