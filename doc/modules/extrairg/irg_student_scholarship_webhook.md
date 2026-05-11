# irg_student_scholarship_webhook

**Categoria:** extrairg  
**Version:** 16.0.1.3.0  
**Licencia:** LGPL-3  
**Instalable:** Si  
**Autor:** IRG  
**Depende de:** `base`, `openeducat_core`, `openeducat_scholarship_enterprise`, `irg_student_scholarship_documents`

---

## Que hace este modulo

Expone un webhook JSON para que una aplicacion externa envie documentacion de solicitudes de beca a Odoo. La aplicacion identifica al alumno/contacto por email y puede enviar tambien el tipo de beca seleccionado.

El tipo de beca se resuelve contra el catalogo oficial de OpenEduCat `op.scholarship.type`, el mismo listado que aparece en **Becas > Tipos de becas** con columna **Monto**.

## Endpoint

`POST /irg/scholarship/webhook/document`

Headers:

```http
Content-Type: application/json
Authorization: Bearer <token>
```


El token se compara con el parametro de sistema `irg_student_scholarship_webhook.token`.

## Payload

```json
{
  "email": "alumno@example.com",
  "filename": "solicitud_beca.pdf",
  "document_name": "Solicitud de beca",
  "document_content_base64": "JVBERi0xLjQK...",
  "scholarship_type_name": "Beca Merito Academico",
  "scholarship_type_key": "merito-academico",
  "note": "Enviado desde la aplicacion externa"
}
```

Campos obligatorios:

- `email`
- `filename`
- `document_content_base64`

Campos opcionales:

- `document_name`: si falta, se usa `filename`.
- `scholarship_type_name`: nombre visible en `op.scholarship.type`.
- `scholarship_type_key`: clave normalizada del nombre; por ejemplo `merito-academico` para `Beca Merito Academico`.
- `note`

## Resolucion de tipo de beca

Si llega `scholarship_type_name` o `scholarship_type_key`, el webhook:

1. Normaliza el valor recibido: minusculas, sin acentos y separadores tipo guion.
2. Busca tipos activos en `op.scholarship.type`.
3. Compara contra el nombre normalizado del tipo de beca.
4. Tambien acepta la clave sin prefijo `beca-`; por ejemplo, `merito-academico` coincide con `Beca Merito Academico`.
5. Si hay una unica coincidencia, asigna el tipo al campo `res.partner.irg_scholarship_type_id`.

Esto evita duplicar tipos en un modelo custom y permite que la app use exactamente los valores del menu **Becas > Tipos de becas**.

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

`action` puede ser `created` o `updated`.

## Errores principales

- `401 missing_token`: falta `Authorization: Bearer`.
- `401 invalid_token`: token incorrecto.
- `400 invalid_json`: body no valido.
- `400 missing_required_field`: faltan campos obligatorios.
- `400 scholarship_type_not_found`: no existe el tipo de beca activo indicado en `op.scholarship.type`.
- `409 ambiguous_scholarship_type`: mas de un tipo coincide.
- `404 partner_not_found`: no hay alumno/contacto con ese email.
- `409 ambiguous_email`: email duplicado.
- `400 invalid_base64`, `empty_file`, `invalid_file_extension`.
- `413 file_too_large`.

## Seguridad

- Ruta `auth='none'` para integracion servidor-servidor.
- CSRF desactivado porque no es un formulario web de Odoo.
- Token Bearer obligatorio antes de cualquier escritura.
- `sudo()` se usa solo despues de validar token, payload, email, tipo de beca y archivo.

## Tests

Tests en [tests/test_scholarship_webhook.py](../../../addons-extra/extrairg/irg_student_scholarship_webhook/tests/test_scholarship_webhook.py):

- Token ausente/invalido.
- Email inexistente o ambiguo.
- Base64, extension y archivo vacio.
- Creacion y actualizacion idempotente de documentos.
- Asignacion de tipo de beca OpenEduCat por nombre, clave y nombre sin acentos.
- Error cuando el tipo de beca no existe.

## Instalacion / Actualizacion

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_student_scholarship_documents,irg_student_scholarship_webhook \
    --stop-after-init --db_host=pgodoo_latest
```

## Ejemplo curl

```bash
curl -X POST https://campus.example.com/irg/scholarship/webhook/document \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mi-token-secreto" \
  -d '{
    "email": "juan.perez@example.com",
    "filename": "dni_frontal.jpg",
    "document_name": "DNI - Cara frontal",
    "scholarship_type_name": "Beca Merito Academico",
    "document_content_base64": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
    "note": "Subido desde formulario de beca"
  }'
```