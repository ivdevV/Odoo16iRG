# Aprendizajes: webhook entrante de documentos de oficialidad

## Contexto

`irg_student_oficialidad_documents` + `irg_student_oficialidad_webhook` reciben desde una app externa los documentos del alumno por `POST /irg/oficialidad/webhook/document` (`auth='none'`, Bearer). Extiende el patron del webhook de becas.

## Decisiones reutilizables

### Confiar en el dato de la app y avisar con el dato de Odoo

`student_type` (nacional/internacional) lo decide la app y se guarda tal cual. El VAT del contacto solo genera un aviso visual (`type_mismatch`); nunca debe rechazar la peticion, porque el VAT de Odoo suele estar vacio o mal. Conviene dejarlo escrito en el contrato para que nadie lo "endurezca" despues.

### Validar el archivo antes de buscar el email

El orden token → JSON → campos → archivo → tipo → email → `sudo()` evita que el endpoint sirva de oraculo de existencia de contactos con payloads invalidos y no hace trabajo caro sin necesidad. El patron de becas resolvia el partner antes que el archivo. Comprobar la longitud del base64 **antes** de decodificar acota la memoria.

### `compare_digest` sobre bytes

`hmac.compare_digest` con `str` no ASCII lanza `TypeError` (un 500 que filtra que la ruta existe). Codificar ambos lados a UTF-8 y capturar `TypeError`/`ValueError` (incluye surrogates sueltos) y devolver 401. Un token configurado vacio o con espacios debe tratarse como "no configurado" y rechazar.

### Idempotencia con `UNIQUE(partner_id, document_type_id)`

La restriccion SQL cubre la carrera concurrente; el servicio hace search + write y, si crea, lo hace en un savepoint: ante `IntegrityError` vuelve a buscar y actualiza. Escribir el campo del contacto (`student_type`) solo tras guardar el documento, en el mismo savepoint, para no dejar escrituras parciales.

### Tests de `HttpCase` con `auth='none'`

Hace falta `self.authenticate(None, None)` para que la ruta resuelva la base de datos. `assertRaises` de Odoo abre un savepoint y puede enmascarar un bug de commit parcial: usar `try/except` para esos casos. Los adjuntos de `Binary(attachment=True)` se buscan con `flush_all()` y `res_field='file'`.

### Sin secretos

El parametro del token se crea vacio con `noupdate="1"` y se rellena por entorno. Los tests usan un token efimero con `set_param` dentro de la transaccion. En logs solo el codigo de rechazo y la clase de la excepcion; nunca payload, email, base64 ni mensaje de excepcion.
