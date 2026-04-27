# irg_forum_disable_karma

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** AGPL-3
**Instalable:** Sí
**Autor:** iRG Developer
**Depende de:** `website_forum`

---

## ¿Qué hace este módulo?

Elimina todos los requisitos de karma en los foros del campus. En Odoo estándar, el foro utiliza el sistema de karma para controlar qué acciones puede realizar cada usuario (votar, publicar, editar, etc.). Este módulo desactiva esas restricciones para que todos los alumnos puedan interactuar libremente en el foro independientemente de su karma acumulado.

La desactivación se realiza mediante un `post_init_hook` que pone a cero los umbrales de karma de todos los foros existentes en el momento de la instalación.

## Funcionalidades principales

- Desactiva todos los requisitos de karma en los foros (preguntar, responder, votar, editar, etc.).
- `post_init_hook` que aplica el cambio automáticamente en la instalación.
- Sin configuración adicional — el módulo actúa directamente sobre el dato.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `forum.forum` | Herencia | Pone a 0 todos los campos `karma_*` |

## Notas técnicas

- Usa `post_init_hook` para resetear los valores de karma en la instalación.
- No añade vistas ni campos visibles al usuario.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_forum_disable_karma \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_forum_disable_karma \
    --stop-after-init --db_host=pgodoo_latest
```
