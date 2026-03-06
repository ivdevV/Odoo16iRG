# Micro-spec: irg_forum_email_notify

## 1. Título
Notificaciones por email en publicaciones del foro

## 2. Resumen
Enviar un correo electrónico automático a todos los participantes elegibles de un foro cuando se crea una nueva publicación (pregunta o respuesta), respetando la configuración de visibilidad del foro (batch / curso). Incluir opción de opt-out por foro.

## 3. Motivo / justificación
Los usuarios del campus no siempre revisan los foros de forma activa. Un email con el contenido completo del mensaje y enlace al hilo garantiza que no se pierdan avisos importantes. Se implementa como módulo extra para no tocar el core de `website_forum`.

## 4. Alcance exacto
- **Modelos**: `forum.forum` (campo `email_notify_enabled`), `forum.post` (override `create()`), `res.users` (campo `forum_email_optout_ids`)
- **Vistas**: Herencia en formulario de `forum.forum` para mostrar checkbox de notificaciones
- **Controllers**: Endpoint `/forum/email/unsubscribe` y `/forum/email/resubscribe` para opt-out/opt-in vía link en email
- **Templates QWeb**: Plantilla HTML del email, páginas de confirmación de (des)suscripción
- **Reports**: Ninguno

## 5. Diseño técnico

### Campos nuevos
| Modelo | Campo | Tipo | Descripción |
|---|---|---|---|
| `forum.forum` | `email_notify_enabled` | Boolean (default True) | Habilita/deshabilita notificaciones email por foro |
| `res.users` | `forum_email_optout_ids` | Many2many → `forum.forum` | Foros de los que el usuario ha cancelado las notificaciones |

### Lógica de destinatarios (`forum.forum._get_notification_recipients()`)
1. Si el foro tiene `visibility_batch_ids` → usuarios cuyos estudiantes pertenecen a esos batches
2. Si el foro tiene `visibility_course_ids` pero no batches → todos los usuarios de esos cursos
3. Si tiene ambos → intersección (usuarios en esos batches Y esos cursos)
4. Si no tiene ninguno → todos los estudiantes activos con usuario
5. Se excluyen: el autor del post, usuarios con opt-out para ese foro, partners sin email

### Envío de emails
- Se crean registros `mail.mail` (estado `outgoing`) en `forum.post.create()`
- El cron nativo de Odoo (`mail.ir_cron_mail_scheduler_action`) envía los emails
- Cada email incluye un enlace de opt-out con token HMAC firmado con `database.secret`

### Opt-out
- Token HMAC: `hmac(database.secret, "forum-unsub-{user_id}-{forum_id}")[:32]`
- Controller público verifica token y añade/quita el foro del M2M
- Páginas de confirmación renderizadas con `website.layout`

## 6. Dependencias
```python
'depends': ['website_forum', 'website', 'openeducat_core', 'irg_forum_batch_visibility']
```

## 7. Backwards-compatibility / migración
No aplica (módulo nuevo). Para desinstalar:
```bash
odoo -d <db> -u irg_forum_email_notify --stop-after-init
# o bien desde Ajustes → Módulos → Desinstalar
```

## 8. Casos de prueba / criterios de aceptación
1. Crear publicación en foro con batch → solo reciben email los alumnos del batch
2. Crear publicación en foro con curso sin batch → reciben email todos los alumnos del curso
3. Crear publicación en foro sin restricciones → todos los alumnos del campus
4. El autor del post NO recibe email
5. Un usuario que hace opt-out NO recibe más emails de ese foro
6. Un usuario que se re-suscribe vuelve a recibir emails
7. El enlace de opt-out con token inválido muestra error
8. El email contiene el texto completo del mensaje y el enlace al hilo

## 9. Rollback plan
```bash
odoo -d <db> --uninstall irg_forum_email_notify --stop-after-init
```

## 10. Estimación y responsable
- Estimación: 4h desarrollo + 1h QA
- Responsable: Equipo IRG
