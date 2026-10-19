# irg_student_oficialidad_webhook

**Categoria:** extrairg  
**Version:** 16.0.1.0.0  
**Licencia:** LGPL-3  
**Instalable:** Si  
**Autor:** IRG  
**Depende de:** `base`, `irg_student_oficialidad_documents`

(`irg_student_oficialidad_documents` depende a su vez de `base`, `openeducat_core` e `isep_control_escolar`.)

---

## Que hace este modulo

Expone un webhook JSON para que la aplicacion externa de oficialidad (Unimarconi) envie a Odoo los documentos de oficialidad de un alumno o contacto. La aplicacion identifica al alumno por email, indica si es `nacional` o `internacional` y el tipo de documento por su clave (`document_type_key`).

El modulo `irg_student_oficialidad_documents` aporta el catalogo de tipos, el modelo de documentos, el resumen `X/4` y el checklist en **Detalle Oficialidad** del alumno. Este modulo solo anade el endpoint y su servicio.

## Endpoint

`POST /irg/oficialidad/webhook/document`

Headers:

```http
Content-Type: application/json
Authorization: Bearer <token>
```

El token se compara con el parametro de sistema `irg_student_oficialidad_webhook.token`. Se instala **vacio** y con `noupdate`: mientras este vacio, el endpoint rechaza todas las peticiones (`401 webhook_token_not_configured`). Hay que configurarlo por entorno en **Ajustes > Tecnico > Parametros del sistema**; nunca se versiona.

## Payload

```json
{
  "email": "alumno@example.com",
  "student_type": "internacional",
  "document_type_key": "pasaporte",
  "filename": "pasaporte.pdf",
  "document_name": "Pasaporte",
  "document_content_base64": "JVBERi0xLjQK...",
  "note": "Enviado desde la aplicacion de oficialidad"
}
```

Campos obligatorios:

- `email` (max. 254 caracteres)
- `student_type`
- `document_type_key` (max. 64 caracteres)
- `filename`
- `document_content_base64`

Campos opcionales:

- `document_name`: si falta, se usa el nombre del tipo de documento (max. 255).
- `note` (max. 2000).

Archivos: extensiones `.pdf`, `.jpg`, `.jpeg`, `.png`, `.doc`, `.docx`; maximo 10 MB decodificados.

### `student_type`

| Valor | Significado |
| --- | --- |
| `nacional` | Alumno con documentacion espanola. |
| `internacional` | Alumno con documentacion extranjera (apostillada). |

La aplicacion es la fuente de verdad del tipo de alumno: Odoo lo guarda en `res.partner.irg_oficialidad_student_type` y calcula el resumen esperado (`X/4`) a partir de el.

### `document_type_key`

Catalogo `irg.oficialidad.document.type` (7 claves):

| Clave | Nombre | Aplica a |
| --- | --- | --- |
| `titulo-universitario` | Titulo universitario | `nacional` |
| `certificado-notas` | Certificado oficial de notas | `nacional` |
| `documento-identificativo-nacional` | DNI / documento identificativo | `nacional` |
| `titulo-universitario-apostillado` | Titulo universitario apostillado | `internacional` |
| `apostilla-certificado-notas` | Apostilla del certificado oficial de notas | `internacional` |
| `pasaporte` | Pasaporte | `internacional` |
| `matricula-unimarconi` | Matricula Unimarconi cumplimentada | ambos |

Cada tipo de alumno espera 4 documentos: los 3 propios de su tipo mas `matricula-unimarconi`.

## Identificacion del alumno y NIF/NIE

El webhook busca primero en `op.student` y luego en `res.partner` por email (insensible a mayusculas; `%` y `_` se tratan como texto literal). Si hay cero o mas de una coincidencia, devuelve error y no escribe nada.

El `student_type` enviado por la app **manda**. Si el VAT del contacto parece un DNI/NIE pero el tipo es `internacional` (o al reves), Odoo solo marca una **advertencia visual** en la ficha del alumno (`irg_oficialidad_type_mismatch`); nunca rechaza la peticion.

## Idempotencia

Existe una restriccion `UNIQUE (partner_id, document_type_id)`. Enviar de nuevo el mismo tipo para el mismo contacto **actualiza** el archivo y los metadatos (no duplica). Un reenvio no cambia el `state` del documento. Una carrera concurrente se resuelve como actualizacion.

## Respuesta correcta

```json
{
  "ok": true,
  "action": "created",
  "document_id": 123,
  "partner_id": 456,
  "student_id": 789
}
```

`action` puede ser `created` o `updated`. `student_id` es `false` si el email solo corresponde a un contacto sin ficha de alumno.

## Errores principales

| HTTP | `error` | Causa |
| --- | --- | --- |
| 401 | `missing_token` | Falta `Authorization: Bearer`. |
| 401 | `invalid_token` | Token incorrecto (incluye tokens con caracteres no ASCII). |
| 401 | `webhook_token_not_configured` | El parametro del token esta vacio o no existe. |
| 400 | `invalid_json` / `invalid_payload` | Body no valido o no es un objeto JSON. |
| 400 | `missing_required_field` | Faltan campos obligatorios. |
| 400 | `invalid_student_type` | `student_type` ausente o distinto de `nacional`/`internacional`. |
| 400 | `invalid_base64`, `empty_file`, `invalid_file_extension` | Archivo no valido. |
| 413 | `file_too_large` | Archivo > 10 MB o cuerpo de la peticion > 15 MB. |
| 404 | `document_type_not_found` | Clave inexistente o inactiva. |
| 409 | `document_type_student_type_mismatch` | El tipo de documento no corresponde al `student_type` (p. ej. `titulo-universitario-apostillado` con `nacional`). |
| 409 | `ambiguous_document_type` | Mas de un tipo con esa clave. |
| 404 | `partner_not_found` | No hay alumno/contacto con ese email. |
| 409 | `ambiguous_email` | Email duplicado. |
| 500 | `server_error` | Error inesperado; respuesta generica sin detalle interno. |

### Orden de validacion

1. Token (nada mas se lee sin token valido).
2. Tamano del cuerpo y JSON.
3. Campos obligatorios y `student_type`.
4. Archivo: longitud del base64 **antes** de decodificar, base64, extension, no vacio, 10 MB.
5. Tipo de documento y compatibilidad con `student_type`.
6. Busqueda del alumno/contacto por email.
7. Escritura con `sudo()`.

El archivo se valida antes que el email, de modo que un email inexistente no se puede usar para sondear contactos con payloads invalidos.

## Seguridad

Controles principales del Security Advisor (C1-C10; ver `missions/irg-student-oficialidad-documents/artifacts/security-advisor.txt`):

- Ruta `auth='none'` para integracion servidor-servidor y CSRF desactivado (no es un formulario Odoo).
- **C1/C2:** token comparado con `hmac.compare_digest` sobre bytes UTF-8; un token no ASCII da `401`, no `500`. Token vacio o con solo espacios = no configurado = rechazo (fail closed).
- **C3:** orden de validacion estricto (arriba); `sudo()` solo tras validar todo.
- **C4:** el email no expande comodines `%`/`_` en la busqueda.
- **C5:** `filename` saneado (basename, sin caracteres de control, longitud acotada); tambien `document_name`, `note`, `email` y `document_type_key`.
- **C6:** `UNIQUE(partner_id, document_type_id)` y `UNIQUE(key)` en el catalogo.
- **C7:** ACL solo para usuarios internos (documentos: CRUD para `base.group_user`; catalogo: lectura para internos y CRUD para administradores); nada para portal o publico; adjuntos privados (`public=False`).
- **C8:** sin PII, payload ni token en logs; el 500 es generico y hace rollback.
- **C9:** tests de seguridad para los casos anteriores.
- **C10:** el token real no esta en el repositorio; el parametro se crea vacio con `noupdate`.
- El `student_type` escrito en el contacto solo se actualiza despues de guardar el documento, en el mismo savepoint.

Riesgos residuales aceptados: un unico token compartido; `student_type` confiado desde la app; un reenvio sobrescribe el archivo anterior sin historial. Recomendado en el proxy: `client_max_body_size` ~14m, limite de peticiones y comprobar `dbfilter` / base unica para la ruta `auth='none'`.

## Tests

- [test_oficialidad_webhook.py](../../../addons-extra/extrairg/irg_student_oficialidad_webhook/tests/test_oficialidad_webhook.py): 66 tests (token, payload, orden de validacion, archivo, email, idempotencia, logs, rollback, HTTP).
- [test_oficialidad_document_types.py](../../../addons-extra/extrairg/irg_student_oficialidad_documents/tests/test_oficialidad_document_types.py) y [test_oficialidad_summary.py](../../../addons-extra/extrairg/irg_student_oficialidad_documents/tests/test_oficialidad_summary.py): 25 tests del catalogo, resumen y permisos.

Validacion de la mision: 91 tests Odoo sin fallos y E2E TestSprite de la vista **Detalle Oficialidad** en verde.

## Instalacion / Actualizacion

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_student_oficialidad_documents,irg_student_oficialidad_webhook \
    --stop-after-init --db_host=pgodoo_latest
```

Despues, configurar el parametro `irg_student_oficialidad_webhook.token` con un secreto aleatorio largo en cada entorno.

## Ejemplo curl

```bash
curl -X POST https://campus.example.com/irg/oficialidad/webhook/document \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer token-de-ejemplo-no-real" \
  -d '{
    "email": "juan.perez@example.com",
    "student_type": "internacional",
    "document_type_key": "pasaporte",
    "filename": "pasaporte.pdf",
    "document_name": "Pasaporte",
    "document_content_base64": "JVBERi0xLjQK...",
    "note": "Subido desde la aplicacion de oficialidad"
  }'
```
