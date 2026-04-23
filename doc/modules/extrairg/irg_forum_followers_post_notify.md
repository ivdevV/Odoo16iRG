# irg_forum_followers_post_notify

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** AGPL-3
**Instalable:** Sí
**Autor:** iRG Developer
**Depende de:** `website_forum`, `irg_forum_post_comments_limit`

---

## ¿Qué hace este módulo?

Notifica a los seguidores de un hilo de foro cuando se publica una nueva respuesta o comentario. Complementa a `irg_forum_email_notify` (que notifica a todos los participantes del foro) añadiendo notificaciones específicas dirigidas a los usuarios que han marcado un post concreto como favorito o lo siguen activamente.

## Funcionalidades principales

- Envía notificación a los seguidores de un post cuando se publica una respuesta.
- Se apoya en el sistema de seguidores (`mail.thread`) de Odoo.
- Integrado con las restricciones de comentarios de `irg_forum_post_comments_limit`.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `forum.post` | Herencia | Lógica de notificación a seguidores |

## Notas técnicas

- Sin archivos de datos adicionales; toda la lógica es Python.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_forum_followers_post_notify \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_forum_followers_post_notify \
    --stop-after-init --db_host=pgodoo_latest
```
