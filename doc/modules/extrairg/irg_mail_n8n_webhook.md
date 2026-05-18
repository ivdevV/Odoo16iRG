# irg_mail_n8n_webhook

**Categoria:** extrairg  
**Version:** 16.0.1.2.0  
**Licencia:** LGPL-3  
**Instalable:** Si  
**Autor:** IRG  
**Depende de:** `base`, `mail`

---

## Que hace este modulo

Redirige el correo saliente de Odoo hacia un webhook de n8n. En lugar de entregar los mensajes mediante el flujo SMTP nativo cuando el conector esta activado, el modulo intercepta `mail.mail.send()` y `mail.mail._send()` para enviar a n8n un payload JSON con los datos del correo, destinatarios, autor, contexto de Odoo y adjuntos codificados en base64.

El objetivo es delegar la entrega real del email en un workflow externo de n8n, manteniendo en Odoo una cola tecnica de entregas con estado, trazabilidad, clave de idempotencia, respuesta HTTP y reintentos. Si el conector esta desactivado, Odoo vuelve a usar el comportamiento nativo de `mail.mail.send()`.

La version 16.0.1.2.0 retira la dependencia dura sobre `mail_smtp_imap_by_company`. Esto es intencional: el modulo no debe provocar instalaciones ni actualizaciones colaterales de addons de SMTP/IMAP por compania. La compatibilidad con ese addon se mantiene interceptando `mail.mail._send()`, porque su override de `send()` termina llamando al flujo interno `_send()`.

No expone controladores HTTP en Odoo: Odoo actua como cliente saliente y n8n como receptor del webhook.

## Funcionalidades principales

- Intercepta el envio de correos de `mail.mail` cuando `irg_mail_n8n_webhook.enabled` esta activo.
- Intercepta tanto `send()` como `_send()` para cubrir envios normales y llamadas directas desde overrides SMTP.
- Crea o reutiliza una entrega tecnica `irg.mail.n8n.delivery` por correo usando una clave de idempotencia estable.
- Envia a n8n un `POST` JSON con cabecera `Authorization: Bearer <token>` y `Idempotency-Key`.
- Registra intentos, estado, URL usada, hash del payload, codigo HTTP, cuerpo de respuesta y motivo de fallo.
- Reintenta automaticamente entregas pendientes o fallidas mediante cron.
- Permite reintentar o cancelar entregas manualmente desde el menu tecnico.
- Limita el tamano maximo de cada adjunto segun parametro configurable.
- Permite activar logs del payload solo para depuracion controlada.

## Manifest y dependencias

| Campo | Valor |
|-------|-------|
| `name` | IRG Mail n8n Webhook |
| `version` | 16.0.1.2.0 |
| `category` | Technical |
| `summary` | Redirige el correo saliente de Odoo a un webhook de n8n |
| `author` | IRG |
| `website` | https://www.irg.edu.es |
| `license` | LGPL-3 |
| `installable` | True |
| `auto_install` | False |
| `application` | False |

Dependencias del manifest:

- `base`: configuracion y modelos base de Odoo.
- `mail`: modelo `mail.mail`, mensajes, destinatarios y postproceso de envio.

No se declara dependencia sobre `mail_smtp_imap_by_company` de forma deliberada. Ese addon es compatible porque su override de `mail.mail.send()` acaba llamando a `mail.mail._send()`, y `irg_mail_n8n_webhook` intercepta ese punto comun del flujo de envio. Mantener solo `base` y `mail` evita que una actualizacion del webhook arrastre la instalacion o actualizacion de modulos SMTP/IMAP ajenos al conector n8n.

Archivos cargados por el manifest:

- `security/ir.model.access.csv`
- `data/config_data.xml`
- `data/cron_data.xml`
- `views/res_config_settings_views.xml`
- `views/irg_mail_n8n_delivery_views.xml`

## Modelos y servicios

| Modelo | Tipo | Campos / metodos principales |
|--------|------|------------------------------|
| `irg.mail.n8n.delivery` | Nuevo | `mail_id`, `state`, `attempt_count`, `next_attempt_at`, `last_attempt_at`, `sent_at`, `idempotency_key`, `webhook_url`, `response_status`, `response_body`, `failure_reason`, `payload_hash`; metodos `action_retry_now()`, `action_cancel()`, `_cron_retry_pending_deliveries()` |
| `irg.mail.n8n.service` | Servicio abstracto nuevo | `_is_enabled()`, `_get_config()`, `_dispatch_mail()`, `_send_delivery()`, `_build_payload()`, `_build_recipients()`, `_build_attachments()`, `_post_json()` |
| `mail.mail` | Herencia | Sobrescribe `send()` y `_send()` para desviar el envio a n8n si el conector esta activado; delega a `super()` si esta desactivado |
| `res.config.settings` | Herencia | Expone parametros de configuracion del webhook en Ajustes |

El modelo `irg.mail.n8n.delivery` tiene una restriccion SQL `unique(idempotency_key)` para evitar duplicar entregas tecnicas del mismo correo. La clave se genera como `odoo-mail-<database>-<mail_id>`.

## Parametros de configuracion

El modulo crea parametros de sistema con `noupdate="1"` y los expone en `res.config.settings`:

| Parametro | Valor inicial | Uso |
|-----------|---------------|-----|
| `irg_mail_n8n_webhook.enabled` | `False` | Activa o desactiva la redireccion de correo a n8n. |
| `irg_mail_n8n_webhook.webhook_url` | vacio | URL del webhook de n8n que recibira los correos. |
| `irg_mail_n8n_webhook.auth_token` | vacio | Token Bearer enviado en la cabecera `Authorization`. |
| `irg_mail_n8n_webhook.timeout` | `15` | Timeout HTTP en segundos; el servicio lo limita entre 1 y 120. |
| `irg_mail_n8n_webhook.max_attempts` | `5` | Intentos maximos antes de marcar el correo como excepcion. |
| `irg_mail_n8n_webhook.max_attachment_mb` | `10` | Tamano maximo por adjunto; el servicio lo limita entre 1 y 100 MB. |
| `irg_mail_n8n_webhook.debug_payload` | `False` | Si esta activo, registra el payload completo en logs. |

Los parametros se leen con `ir.config_parameter.sudo()` porque son configuracion tecnica global del sistema.

## Vistas y UI

El modulo anade un bloque **IRG Mail n8n** en el formulario general de ajustes de Odoo (`base.res_config_settings_view_form`). Desde ahi se pueden configurar activacion, URL, token, timeout, intentos maximos, limite de adjuntos y logging del payload.

Tambien crea vistas de lista y formulario para `irg.mail.n8n.delivery`:

- Lista con fecha, correo Odoo, estado, intentos, proximo intento, estado HTTP y clave de idempotencia.
- Formulario con botones **Reintentar** y **Cancelar**, statusbar de estado y pestana de respuesta tecnica.
- Accion `Entregas n8n` bajo el menu tecnico **Administracion > Mail n8n > Entregas**, restringido a administradores del sistema.

## Cron

El cron `IRG: Retry n8n mail webhook deliveries` ejecuta:

```python
model._cron_retry_pending_deliveries()
```

Configuracion:

- Modelo: `irg.mail.n8n.delivery`
- Frecuencia: cada 5 minutos
- Usuario: `base.user_root`
- Activo: si
- `doall`: `False`

El cron procesa hasta 50 entregas por ejecucion en estado `pending` o `failed` cuando `next_attempt_at` esta vacio o ya vencido. Si el conector esta desactivado, no procesa la cola.

## Flujo operativo

1. Odoo crea un registro `mail.mail` y llama a `send()` o `_send()` segun el flujo de correo activo.
2. Si `irg_mail_n8n_webhook.enabled` esta desactivado, se usa el envio nativo de Odoo.
3. Si esta activado, el servicio crea o recupera una entrega `irg.mail.n8n.delivery` con clave de idempotencia.
4. Si la entrega ya esta `sent`, el correo se marca como `sent` y no se reenvia.
5. El servicio valida que existan URL y token, construye el payload y calcula `payload_hash` con SHA-256.
6. Odoo envia un `POST` JSON a n8n con timeout configurable.
7. Si n8n responde con HTTP `2xx`, la entrega y el correo pasan a `sent` y se ejecuta el postproceso normal de mensaje enviado.
8. Si hay error HTTP, error de conexion, configuracion incompleta o adjunto demasiado grande, se registra el fallo y se agenda reintento.
9. Cuando se agotan los intentos, el correo pasa a `exception` y la entrega queda `failed` sin proximo intento.

## Payload enviado a n8n

El webhook recibe JSON con esta estructura principal:

```json
{
  "idempotency_key": "odoo-mail-<database>-<mail_id>",
  "odoo": {
    "database": "<dbname>",
    "base_url": "https://odoo.example.com",
    "company_id": 1,
    "company_name": "Compania"
  },
  "mail": {
    "id": 123,
    "message_id": "<message-id>",
    "mail_message_id": 456,
    "model": "sale.order",
    "res_id": 789,
    "subject": "Asunto",
    "body_html": "<p>Contenido</p>",
    "email_from": "odoo@example.com",
    "reply_to": "reply@example.com",
    "email_to": "destino@example.com",
    "email_cc": "copia@example.com",
    "auto_delete": false
  },
  "recipients": [
    {
      "partner_id": 10,
      "name": "Alumno",
      "email": "alumno@example.com",
      "type": "to"
    }
  ],
  "author": {
    "id": 20,
    "name": "Autor",
    "email": "autor@example.com"
  },
  "attachments": [
    {
      "id": 30,
      "name": "documento.pdf",
      "mimetype": "application/pdf",
      "size": 12345,
      "content_base64": "JVBERi0xLjQK..."
    }
  ],
  "created_at": "2026-05-18 10:00:00"
}
```

Cabeceras HTTP enviadas:

```http
Content-Type: application/json; charset=utf-8
Authorization: Bearer <token>
Idempotency-Key: odoo-mail-<database>-<mail_id>
```

Los destinatarios pueden salir de `recipient_ids`, `email_to` y `email_cc`. Los adjuntos se leen desde `attachment_ids`, se decodifican para medir tamano real y se vuelven a enviar como base64.

## Reintentos y errores

El contador `attempt_count` se incrementa antes de cada intento de envio. Si el intento falla y no se han agotado los intentos maximos, la entrega queda en `failed` con `next_attempt_at` calculado mediante backoff exponencial:

| Intento fallido | Retraso aproximado |
|-----------------|--------------------|
| 1 | 1 minuto |
| 2 | 2 minutos |
| 3 | 4 minutos |
| 4 | 8 minutos |
| N | Hasta un maximo de 60 minutos |

Casos que programan reintento:

- URL o token no configurados.
- Error al construir el payload, por ejemplo adjunto mayor que el limite configurado.
- Error de red o timeout al contactar con n8n.
- Respuesta HTTP fuera de rango `2xx`.

Cuando `attempt_count` alcanza `irg_mail_n8n_webhook.max_attempts`, la entrega queda `failed`, `next_attempt_at` se limpia y el `mail.mail` asociado pasa a estado `exception` con `failure_reason`.

## Seguridad

- Solo el grupo `base.group_system` tiene acceso CRUD al modelo `irg.mail.n8n.delivery`.
- Los menus de entregas estan restringidos a administradores del sistema.
- El token se guarda como parametro de sistema y se muestra como campo password en ajustes.
- La autenticacion hacia n8n se realiza mediante `Authorization: Bearer <token>`.
- No se exponen endpoints publicos en Odoo.
- El cron usa `sudo()` para procesar una cola tecnica independientemente del usuario que origino el correo.
- El payload puede contener HTML, emails y adjuntos; `debug_payload` debe mantenerse desactivado salvo depuracion puntual.

## Tests

Tests en [tests/test_mail_n8n_webhook.py](../../../addons-extra/extrairg/irg_mail_n8n_webhook/tests/test_mail_n8n_webhook.py):

- Construccion del payload con datos principales del correo.
- Marcado de correo y entrega como enviados ante respuesta HTTP `2xx`.
- Programacion de reintento ante error HTTP.
- Paso del correo a `exception` cuando se agotan los intentos.
- Delegacion al envio nativo cuando el modulo esta desactivado.

Los tests estan etiquetados como `post_install` y `-at_install`.

## Instalacion y activacion

Instalar o actualizar el modulo:

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_mail_n8n_webhook \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_mail_n8n_webhook \
    --stop-after-init --db_host=pgodoo_latest
```

Activacion funcional:

1. Ir a **Ajustes > IRG Mail n8n**.
2. Configurar `URL webhook n8n` y `Token Bearer n8n`.
3. Ajustar timeout, intentos maximos y limite de adjuntos si aplica.
4. Activar **Enviar correos por n8n**.
5. Enviar un correo de prueba y revisar **Administracion > Mail n8n > Entregas**.

Comprobacion operativa en servidor tras actualizar el modulo:

1. Verificar que el parametro `irg_mail_n8n_webhook.enabled` esta en `True`.
2. Confirmar que `irg_mail_n8n_webhook.webhook_url` y `irg_mail_n8n_webhook.auth_token` estan configurados.
3. Enviar una solicitud de firma de Odoo Sign para generar un correo real del flujo operativo.
4. Revisar **Administracion > Mail n8n > Entregas** y confirmar que aparece una entrega asociada al correo.
5. Si el email sigue saliendo por SMTP, revisar que el modulo se haya actualizado correctamente a la version 16.0.1.2.0 y que la intercepcion de `_send()` este activa.

### Nota sobre errores ajenos durante actualizaciones

Durante un intento de actualizacion se observo un error de validacion del servidor relacionado con la clave foranea `op_subject_registration_student_id_fkey`. Ese error no pertenece a `irg_mail_n8n_webhook`: apunta a un problema de integridad de datos de OpenEduCat durante un intento de instalar o actualizar otras dependencias.

La accion recomendada es traer este fix al servidor y actualizar unicamente `irg_mail_n8n_webhook`, sin forzar la instalacion ni la actualizacion de dependencias adicionales no relacionadas.

## Rollback operativo

Para volver al comportamiento nativo de Odoo sin desinstalar el modulo, desactivar `irg_mail_n8n_webhook.enabled` desde ajustes o parametros de sistema. Desde ese momento `mail.mail.send()` y `mail.mail._send()` delegan en el flujo original de Odoo.

Si hay entregas fallidas o pendientes que no deben reenviarse, cancelarlas desde **Administracion > Mail n8n > Entregas** con el boton **Cancelar**. El cron no procesa entregas cuando el conector esta desactivado.

## Limitaciones conocidas

- La instalacion/actualizacion en Docker y los tests Odoo no se ejecutaron durante esta documentacion porque el daemon de Docker no estaba disponible.
- El modulo no valida el formato de la URL del webhook antes de intentar el envio.
- El limite de adjuntos aplica por adjunto individual, no al tamano total del payload.
- Si `debug_payload` esta activo, el log puede contener datos personales, HTML del mensaje y adjuntos codificados.

## Notas tecnicas

- Usa `urllib.request` de la libreria estandar para realizar el `POST` a n8n.
- Trunca el cuerpo de respuesta HTTP almacenado a 2000 caracteres.
- Calcula `payload_hash` sobre el JSON ordenado para facilitar trazabilidad tecnica.
- El envio se considera correcto con cualquier estado HTTP `2xx`.
- En caso de exito ejecuta `_postprocess_sent_message()` con los destinatarios del correo.
- En fallo definitivo ejecuta `_postprocess_sent_message()` con `failure_type='mail_smtp'` para mantener compatibilidad con la semantica de fallo de correo de Odoo.