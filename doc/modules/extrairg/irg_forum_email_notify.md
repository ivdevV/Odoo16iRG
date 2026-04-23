# irg_forum_email_notify

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `website_forum`, `website`, `openeducat_core`, `irg_forum_batch_visibility`

---

## ¿Qué hace este módulo?

Envía notificaciones por correo electrónico a todos los participantes elegibles de un foro cada vez que se publica una nueva entrada (pregunta o respuesta). El módulo determina los destinatarios según la configuración de visibilidad del foro (por lote o por curso), asegurando que cada alumno reciba solo los mensajes relevantes para su grupo.

Cada correo incluye el contenido completo de la publicación, un enlace directo al hilo del foro y un enlace de baja en un solo clic (unsubscribe).

## Funcionalidades principales

- Envío automático de email al publicar una nueva pregunta o respuesta en el foro.
- Filtrado de destinatarios por visibilidad de foro (batch/course) definida en `irg_forum_batch_visibility`.
- Plantilla de correo personalizable con el contenido del post y enlace al hilo.
- Enlace de baja incluido en cada notificación.
- Configuración adicional en el formulario del foro (campos de notificación).

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `forum.forum` | Herencia | Configuración de notificaciones por email |
| `forum.post` | Herencia | Lógica de disparo del envío de email al publicar |

## Vistas y UI

Añade campos de configuración de notificación en el formulario del foro (`views/forum_forum_views.xml`).

## Dependencias externas

- `irg_forum_batch_visibility` — provee la lógica de visibilidad por lote para determinar destinatarios.
- `openeducat_core` — referencia a `op.batch` para filtrar alumnos.

## Notas técnicas

- Utiliza `data/mail_template.xml` para la plantilla de correo; puede personalizarse desde la interfaz.
- El envío se realiza de forma síncrona al publicar el post.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_forum_email_notify \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_forum_email_notify \
    --stop-after-init --db_host=pgodoo_latest
```
