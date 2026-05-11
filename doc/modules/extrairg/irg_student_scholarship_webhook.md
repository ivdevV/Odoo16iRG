# irg_student_scholarship_webhook

**Categoría:** extrairg  
**Versión:** 16.0.1.0.0  
**Licencia:** LGPL-3  
**Instalable:** Sí  
**Autor:** IRG  
**Depende de:** `base`, `openeducat_core`, `irg_student_scholarship_documents`

---

## ¿Qué hace este módulo?

Proporciona un endpoint HTTP seguro que permite a aplicaciones externas enviar documentación de solicitudes de becas para alumnos y contactos identificándolos por email. Este webhook es útil cuando sistemas externos (portales de inscripción, formularios web) necesitan enviar archivos de forma automatizada sin pasar por la interfaz de Odoo.

El módulo valida la autenticación mediante token Bearer, verifica el formato del archivo, busca al alumno o contacto por email, y crea o actualiza el documento de beca correspondiente. Si ya existe un documento con el mismo partner, nombre y filename, lo actualiza en lugar de duplicarlo.

## Funcionalidades principales

- Endpoint REST público (autenticación por token) en `/irg/scholarship/webhook/document`.
- Validación de token Bearer configurable desde parámetros del sistema.
- Búsqueda de alumno o contacto por email (normalizado, case-insensitive).
- Decodificación y validación de archivos en base64 (extensiones permitidas: PDF, JPG, JPEG, PNG, DOC, DOCX).
- Límite de tamaño de archivo: 10 MB.
- Creación o actualización de documentos de beca (`irg.scholarship.document`) asociados al partner encontrado.
- Respuestas JSON detalladas con códigos de estado HTTP apropiados (200, 400, 401, 404, 409, 413, 500).

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.scholarship.webhook.service` | Abstracto (nuevo) | Servicio que encapsula la lógica de validación y procesamiento del webhook |

El servicio no tiene campos propios; expone métodos para validar autorización y procesar el payload JSON recibido.

## Controladores / Endpoints

### POST `/irg/scholarship/webhook/document`

- **Autenticación:** Ninguna (`auth='none'`), validación manual por token Bearer.
- **CSRF:** Deshabilitado (`csrf=False`).
- **Headers requeridos:**
  - `Authorization: Bearer <token>` — el token debe coincidir con el parámetro del sistema `irg_student_scholarship_webhook.token`.
- **Body (JSON):**
  ```json
  {
    "email": "alumno@example.com",
    "filename": "solicitud_beca.pdf",
    "document_content_base64": "<contenido en base64>",
    "document_name": "Solicitud de Beca 2024",
    "note": "Enviado desde portal externo"
  }
  ```
  - **Campos obligatorios:** `email`, `filename`, `document_content_base64`
  - **Campos opcionales:** `document_name` (por defecto usa `filename`), `note`

- **Respuesta exitosa (200):**
  ```json
  {
    "ok": true,
    "action": "created",
    "document_id": 123,
    "partner_id": 456,
    "student_id": 789
  }
  ```
  - `action` puede ser `"created"` o `"updated"`.
  - `student_id` es `false` si el partner no es un alumno.

- **Errores posibles:**
  - `401 missing_token` / `invalid_token`: Token Bearer no válido o ausente.
  - `400 invalid_json`: El body no es JSON válido.
  - `400 missing_required_field`: Falta `email`, `filename` o `document_content_base64`.
  - `400 invalid_base64`: El campo `document_content_base64` no es base64 válido.
  - `400 invalid_file_extension`: Formato de archivo no permitido (debe ser PDF, JPG, PNG, DOC o DOCX).
  - `400 empty_file`: El archivo decodificado está vacío.
  - `413 file_too_large`: El archivo supera los 10 MB.
  - `404 partner_not_found`: No se encontró ningún alumno o contacto con ese email.
  - `409 ambiguous_email`: Hay más de un alumno o contacto con ese email.
  - `500 server_error`: Error inesperado en el servidor.

## Vistas y UI

Este módulo no añade vistas ni interfaz de usuario. Toda la interacción es por API REST.

## Dependencias externas

- **`openeducat_core`**: Modelo `op.student` para buscar alumnos por email.
- **`irg_student_scholarship_documents`**: Modelo `irg.scholarship.document` donde se almacenan los documentos de becas.

## Notas técnicas

### Configuración del token

El token de autenticación se configura en **Ajustes técnicos → Parámetros del sistema**:

- **Clave:** `irg_student_scholarship_webhook.token`
- **Valor:** (el token secreto compartido con la aplicación externa)

Si el parámetro no existe, el webhook devolverá `webhook_token_not_configured`.

### Uso de `sudo()`

El controlador usa `auth='none'` porque el webhook es invocado desde sistemas externos sin sesión de usuario Odoo. El uso de `sudo()` está justificado porque:

1. Se valida el token Bearer antes de cualquier operación de escritura.
2. Se valida la existencia del partner/alumno por email.
3. Se valida el contenido del archivo (formato, tamaño, extensión).
4. Solo después de todas estas validaciones se permite crear/actualizar el documento de beca.

Este patrón es el estándar para webhooks públicos en Odoo: autenticación manual + `sudo()` tras validación.

### Extensiones permitidas

Definidas en `ALLOWED_EXTENSIONS`:

```python
{'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
```

### Límite de tamaño

Definido en `MAX_FILE_SIZE_BYTES`:

```python
10 * 1024 * 1024  # 10 MB
```

### Lógica de duplicados

El webhook busca documentos existentes con la misma combinación de:

- `partner_id`
- `filename`
- `name` (document_name)

Si existe, actualiza el documento. Si no, crea uno nuevo. Esto evita duplicados cuando se reenvía la misma documentación.

## Tests

El módulo incluye suite completa de tests unitarios en [tests/test_scholarship_webhook.py](../../../addons-extra/extrairg/irg_student_scholarship_webhook/tests/test_scholarship_webhook.py):

- `test_validate_authorization_requires_bearer_token`: Verifica que se rechace petición sin header Authorization.
- `test_validate_authorization_rejects_invalid_token`: Verifica que se rechace token incorrecto.
- `test_process_payload_rejects_unknown_email`: Verifica error 404 si el email no existe.
- `test_process_payload_rejects_invalid_base64`: Verifica error 400 si el base64 es inválido.
- `test_process_payload_rejects_invalid_extension`: Verifica error 400 si la extensión no es permitida.
- `test_process_payload_creates_scholarship_document`: Verifica creación exitosa de documento.
- `test_process_payload_updates_existing_document`: Verifica actualización de documento duplicado.

Para ejecutar los tests:

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> --test-tags=irg_student_scholarship_webhook \
    --stop-after-init --db_host=pgodoo_latest
```

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_student_scholarship_webhook \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_student_scholarship_webhook \
    --stop-after-init --db_host=pgodoo_latest
```

## Rollback / Desinstalación

Para desinstalar el módulo sin perder datos:

1. Documenta el valor del parámetro `irg_student_scholarship_webhook.token` antes de desinstalar.
2. Los documentos de beca creados por el webhook permanecerán en la base de datos (modelo del módulo `irg_student_scholarship_documents`).
3. Desinstala desde la interfaz de Odoo o:

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> --uninstall=irg_student_scholarship_webhook \
    --stop-after-init --db_host=pgodoo_latest
```

El parámetro del sistema debe eliminarse manualmente si se quiere retirar tambien el secreto compartido.

## Ejemplo de uso desde aplicación externa

```bash
curl -X POST https://campus.example.com/irg/scholarship/webhook/document \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mi-token-secreto" \
  -d '{
    "email": "juan.perez@example.com",
    "filename": "dni_frontal.jpg",
    "document_name": "DNI - Cara frontal",
    "document_content_base64": "/9j/4AAQSkZJRgABAQEAYABgAAD...",
    "note": "Subido desde formulario de beca"
  }'
```
