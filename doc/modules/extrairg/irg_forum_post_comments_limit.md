# irg_forum_post_comments_limit

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** AGPL-3
**Instalable:** Sí
**Autor:** iRG Developer
**Depende de:** `website_forum`

---

## ¿Qué hace este módulo?

Permite limitar el número de comentarios y respuestas permitidas en posts específicos del foro. Es útil para foros de clase donde se quiere controlar la participación o evitar hilos excesivamente largos.

Añade un campo en el post del foro para configurar el límite y un template frontend que muestra el límite al usuario.

## Funcionalidades principales

- Campo `max_comments` (o similar) en `forum.post` para definir el límite de respuestas.
- Template frontend que muestra el estado del límite.
- Bloqueo de nuevas respuestas cuando se alcanza el límite configurado.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `forum.post` | Herencia | Campo de límite de comentarios |

## Vistas y UI

- `views/forum_post_views.xml` — campo de límite en el backend.
- `views/forum_post_templates.xml` — indicador de límite en el frontend.

## Notas técnicas

- Es dependencia de `irg_forum_followers_post_notify`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_forum_post_comments_limit \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_forum_post_comments_limit \
    --stop-after-init --db_host=pgodoo_latest
```
