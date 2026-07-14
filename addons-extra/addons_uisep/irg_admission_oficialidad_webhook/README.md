# IRG Admission Oficialidad Webhook

Módulo Odoo 16 que permite enviar a un webhook n8n la información de las
admisiones seleccionadas de un registro de admisión. n8n consume el JSON y se
encarga de actualizar el Google Sheet de oficialidad; Odoo no genera ningún
Excel.

## Dependencias e instalación

Dependencias Odoo:

- `openeducat_core`
- `openeducat_admission`

No añade dependencias Python externas: el transporte HTTP usa la librería
estándar (`urllib`).

Para instalarlo:

1. Desplegar el directorio `irg_admission_oficialidad_webhook` en una ruta de
   addons incluida en `addons_path`.
2. Actualizar la lista de aplicaciones.
3. Instalar **IRG Admission Oficialidad Webhook** o actualizarlo con `-u
   irg_admission_oficialidad_webhook`.
4. Configurar los tres parámetros de sistema antes del primer envío.

## Configuración

Crear o editar los siguientes registros desde **Ajustes > Técnico > Parámetros >
Parámetros del sistema**. El XML del módulo crea las claves en `noupdate` con URL
y token vacíos, por lo que un despliegue o una actualización no debe incluir
credenciales reales en el repositorio.

| Clave exacta | Obligatorio | Valor |
| --- | --- | --- |
| `irg_oficialidad_webhook.webhook_url` | Sí | URL pública HTTPS del webhook n8n, por ejemplo `https://n8n.example.org/webhook/oficialidad`. No admite credenciales embebidas, fragmentos, `localhost`, redes privadas/reservadas ni redirecciones. |
| `irg_oficialidad_webhook.auth_token` | Sí | Secreto compartido. Odoo lo envía como `Authorization: Bearer <token>`. n8n debe validarlo en el servidor antes de procesar el cuerpo. |
| `irg_oficialidad_webhook.timeout` | No | Segundos de espera. Valor predeterminado: `15`. Cualquier valor se limita al intervalo `1`–`120`; un valor no numérico vuelve a `15`. |

El token se almacena en `ir.config_parameter`, se lee con `sudo()` únicamente en
el servicio y no se incluye en el payload ni en los mensajes de error. Debe
considerarse un secreto de base de datos: limitar el acceso a Ajustes/Técnico,
proteger copias de seguridad y rotarlo tanto en Odoo como en n8n.

## Permisos

Solo los usuarios del grupo **Administrador de admisiones**
(`openeducat_admission.group_op_admission_admin`) pueden:

- ver el botón y la acción **Oficialidad**;
- crear, leer, editar o eliminar registros transitorios del wizard;
- abrir el wizard o llamar al servicio de envío.

El servidor vuelve a comprobar el grupo, el modelo activo, la pertenencia de las
admisiones al registro abierto y los permisos/reglas de lectura y escritura. Las
restricciones no dependen del dominio o de la visibilidad del botón en el cliente.
El superusuario de Odoo conserva su bypass estándar.

## Uso

1. Abrir **Admisiones > Registros de admisión** y entrar en un registro.
2. Pulsar **Oficialidad** en la cabecera.
3. Revisar las admisiones precargadas. Se muestran número de aplicación, nombre,
   estado y última fecha de envío; se pueden retirar líneas antes de enviar.
4. Pulsar **Enviar**.
5. Si el webhook responde con HTTP 2xx, Odoo muestra una notificación y escribe
   `oficialidad_sent_date` únicamente en las admisiones seleccionadas. La columna
   **Última oficialidad enviada** también está disponible como columna opcional en
   el registro.

Una selección vacía, una configuración incompleta, una admisión de otro registro,
un destino inseguro, un fallo de conexión o una respuesta no 2xx producen un
`UserError`. En esos casos no se actualiza la fecha y el usuario puede corregir la
causa y reenviar manualmente.

## Payload

El cuerpo usa UTF-8 y `Content-Type: application/json; charset=utf-8`:

```json
{
  "odoo": {
    "database": "<database>",
    "base_url": "https://odoo.example.org",
    "company_id": 1,
    "company_name": "<company>"
  },
  "register": {
    "id": 123,
    "name": "<register>",
    "period": "<period>",
    "course_id": 45,
    "course_name": "<course>",
    "start_date": "2026-01-01",
    "end_date": "2026-12-31"
  },
  "students": [
    {
      "admission": {"id": 1001, "application_number": "<number>"},
      "student": {"id": 2001, "name": "<student>"},
      "partner": {"id": 3001, "name": "<partner>"}
    }
  ],
  "sent_at": "2026-07-14 13:00:00",
  "sent_by": {"user_id": 2, "user_name": "<user>"}
}
```

Los objetos `admission`, `student` y `partner` del ejemplo están abreviados. En la
petición real, el serializador recorre dinámicamente los campos de `op.admission`,
`op.student` y `res.partner` para enviar todos los valores escalares, fechas y
relaciones soportadas. Un estudiante o contacto ausente se representa con `{}`.

Por seguridad y tamaño, “serialización completa” no incluye:

- campos `binary` o `image`;
- campos técnicos de mensajería, actividad, acceso y adjuntos;
- campos cuyo nombre parezca una credencial (`token`, `secret`, `password`,
  `passwd`, `apikey`, `privatekey` o `credential`, incluso con separadores);
- tipos de campo no soportados o campos cuya lectura individual falle.

Las relaciones `many2one`, `many2many` y `one2many` se reducen a `id` y nombre
visible; no se serializan recursivamente.

## Seguridad y hardening

- Autorización de administrador verificada también en servidor.
- Bearer token fuera del payload y errores sanitizados, sin cuerpo remoto ni
  detalle interno de conexión.
- Solo HTTPS; se rechazan destinos locales, privados, reservados o no globales.
- La resolución DNS se valida antes del envío y la conexión se fija a la IP
  validada, conservando el hostname original para SNI y certificado TLS. Esto
  mitiga SSRF y DNS rebinding/TOCTOU.
- No se usan proxies del entorno y no se siguen redirecciones HTTP.
- La respuesta se lee con un límite de 2001 bytes y se conserva como máximo 2000.
- El timeout está acotado entre 1 y 120 segundos.

n8n debe validar el Bearer token en el servidor con comparación segura, responder
con 2xx solo después de aceptar el trabajo y aplicar sus propios límites de tamaño,
registro, autorización y protección frente a reenvíos. El módulo no ofrece firma
HMAC, mTLS ni identificador idempotente.

## Gobierno de PII

El payload contiene información personal extensa porque el contrato funcional
delega en n8n la selección de columnas. Antes de habilitarlo en producción, el
responsable del tratamiento debe:

- documentar finalidad, base jurídica y destinatarios;
- aprobar qué campos necesita realmente n8n/Google Sheets y revisar el payload
  cuando otros módulos añadan campos a los modelos serializados;
- aplicar minimización y borrado/retención en n8n, historial de ejecuciones,
  Google Sheets, logs, copias de seguridad y entornos de prueba;
- limitar y auditar el acceso al grupo de administradores de admisiones, a n8n y
  al documento de destino;
- cifrar el tránsito y los soportes, gestionar incidentes y formalizar los
  acuerdos con encargados/subencargados que correspondan;
- no registrar cuerpos, tokens ni ejemplos con datos reales en tickets, logs o
  documentación.

El filtrado de secretos reduce exposición accidental, pero no convierte el payload
en datos anonimizados ni sustituye una revisión periódica de privacidad.

## Pruebas y validación

La suite Odoo está en `tests/test_oficialidad_webhook.py`, etiquetada como
`post_install` y `-at_install`. Cubre 21 escenarios: wizard y permisos, payload y
serialización robusta, respuestas 2xx/no 2xx, configuración, selección, SSRF,
redirecciones, límite de respuesta, pinning DNS/TLS y sanitización de errores.

La misión fue validada con `docker-compose.local.yml` sobre `test_irg_db`, montando
este worktree como addons de solo lectura. Resultado registrado: actualización del
módulo correcta y **21 tests, 0 fallos, 0 errores**. La evidencia está en
`missions/oficialidad-webhook/artifacts/` y el contrato de cierre en
`missions/oficialidad-webhook/verification.json`.

## Limitaciones conocidas

- Envío manual y síncrono: no hay cola, reintentos automáticos ni backoff.
- No existe historial persistente de intentos o respuestas; solo se guarda la última
  fecha 2xx en la admisión.
- No hay idempotencia: reenviar puede duplicar trabajo si n8n no deduplica.
- Una respuesta 2xx seguida de un fallo de transacción en Odoo puede dejar n8n
  procesado sin fecha local; el sistema no implementa transacción distribuida.
- La disponibilidad depende de DNS, salida HTTPS y de que todas las direcciones
  resueltas sean globales. No se admiten webhooks internos o detrás de redirecciones.
- El primer IP global resuelto queda fijado durante esa petición; el balanceo DNS
  se vuelve a evaluar en el siguiente envío.
- Los cambios futuros en los modelos pueden ampliar el payload de PII. El filtro por
  nombre de secreto es defensa en profundidad y no detecta cualquier nombre posible.
- No hay pantalla específica de configuración ni visor de entregas.
