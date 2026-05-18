# irg_mail_n8n_webhook

## 1. Titulo corto

Redireccion global de correos Odoo a n8n.

## 2. Resumen objetivo

Crear un modulo tecnico que intercepte los correos salientes de Odoo antes de usar SMTP y los envie a un webhook de n8n. El modulo debe conservar una cola propia de reintentos para evitar perdidas o duplicados cuando n8n no responda correctamente.

## 3. Motivo / justificacion

El envio de correo en Odoo se centraliza en `mail.mail`, tanto para plantillas como para notificaciones, crons y llamadas con `force_send=True`. La integracion se implementa con `_inherit` en un modulo extra para no modificar Odoo core ni los modulos funcionales existentes, y para poder activar/desactivar la redireccion desde configuracion.

## 4. Alcance exacto

- Nuevo modulo tecnico `irg_mail_n8n_webhook` en `addons-extra/extrairg/`.
- Herencia de `mail.mail` para redirigir el envio saliente.
- Nuevo modelo tecnico `irg.mail.n8n.delivery` para registrar estado, intentos y errores.
- Servicio tecnico `irg.mail.n8n.service` para construir payloads y llamar a n8n.
- Vista de ajustes en `res.config.settings` con parametros de n8n.
- Cron de reintentos para entregas fallidas o pendientes.
- Tests de servicio, payload, redireccion y reintentos.
- No modifica correo entrante, fetchmail, plantillas existentes ni modulos nativos.

## 5. Diseno tecnico

- `mail.mail.send(auto_commit=False, raise_exception=False)` y `mail.mail._send(...)` se heredan para interceptar el envio central y cubrir overrides SMTP de terceros que llamen directamente a `_send()`.
- Si `irg_mail_n8n_webhook.enabled` esta desactivado, se delega en `super()` y SMTP funciona como hasta ahora.
- Si esta activado, cada `mail.mail` crea o reutiliza una entrega `irg.mail.n8n.delivery` con clave idempotente `odoo-mail-<db>-<mail_id>`.
- El servicio envia un `POST` JSON al webhook de n8n con `Authorization: Bearer <token>` y cabecera `Idempotency-Key`.
- Al recibir respuesta 2xx de n8n, el correo se marca como `sent` y la entrega como `sent`.
- En errores temporales, la entrega queda `failed` con `next_attempt_at` y el correo permanece `outgoing` hasta agotar reintentos.
- Al agotar reintentos, el correo queda en `exception` con `failure_reason` legible.
- Los adjuntos se incluyen en base64 con nombre, mimetype y tamano, respetando un limite configurable.
- Las llamadas a `sudo()` se limitan a lectura/escritura tecnica de parametros y entregas, justificadas porque el envio de correo lo ejecuta el scheduler o integraciones sin usuario funcional estable.

## 6. Dependencias

`base`, `mail`.

No se declara una dependencia dura con `mail_smtp_imap_by_company` para evitar instalaciones o actualizaciones colaterales de ese addon y sus dependencias. La compatibilidad se cubre interceptando tambien `mail.mail._send()`, ya que el override SMTP por compania termina llamando a `_send()` antes de entregar por SMTP.

## 7. Backwards-compatibility / migracion

El modulo esta desactivado por defecto mediante `irg_mail_n8n_webhook.enabled=False`, por lo que instalarlo no altera el envio SMTP hasta configurar y activar la integracion. Si se desactiva el parametro, el flujo vuelve a SMTP nativo sin desinstalar el modulo. El modelo nuevo solo registra entregas tecnicas y no modifica tablas nativas salvo campos heredados por estado de correo durante el envio.

## 8. Casos de prueba / criterios de aceptacion

- Con la redireccion desactivada, `mail.mail.send()` delega en el flujo nativo.
- Con redireccion activada y configuracion incompleta, el correo queda en error controlado.
- Con webhook 2xx, se crea entrega n8n, se envia un payload completo y el correo queda `sent`.
- Los correos de Firma que pasan por el override SMTP por compania no abren SMTP cuando la redireccion n8n esta activa.
- Con webhook 5xx o excepcion de red, se incrementan intentos y se programa reintento.
- Al agotar intentos, el correo queda `exception` con motivo.
- `force_send=True`, plantillas, `message_post()` y crons quedan cubiertos porque todos pasan por `mail.mail`.
- Los adjuntos se incluyen en el payload y se rechazan si superan el limite configurable.
- La clave de idempotencia evita duplicados en n8n.

## 9. Rollback plan

Desactivar primero el parametro desde Ajustes o shell:

```bash
docker exec odoo_latest odoo shell -c /etc/odoo/odoo.conf -d <dbname> --db_host=pgodoo_latest
env['ir.config_parameter'].sudo().set_param('irg_mail_n8n_webhook.enabled', 'False')
```

Si se requiere retirada completa, desinstalar `irg_mail_n8n_webhook` desde Apps. Al estar desacoplado, el rollback no elimina correos ni plantillas existentes.

## 10. Estimacion y responsable

- Estimacion: 1 jornada tecnica para implementacion, pruebas y validacion en staging con n8n.
- Responsable: IRG / GitHub Copilot como asistente de implementacion.