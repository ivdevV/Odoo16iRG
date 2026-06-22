# irg_forum_notice_popup

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `website`, `website_forum`, `irg_campus_course_forum`

---

## ¿Qué hace este módulo?

Muestra avisos o notificaciones importantes del foro del campus como popups filtrados por lote. Permite al equipo docente o administrativo publicar anuncios que aparecen como ventanas emergentes solo a los alumnos del lote correspondiente cuando acceden al foro de su curso.

El popup respeta tanto la visibilidad del foro como la visibilidad granular configurada en cada publicación mediante `irg_forum_batch_visibility`.

Incluye un override del comportamiento de compartir (`forum_share_override`) para personalizar cómo se comparten los posts desde el popup.

## Funcionalidades principales

- Modelo dedicado para avisos de foro (gestión desde el backoffice).
- Popup automático en el frontend cuando hay avisos activos para el lote del alumno.
- Filtrado por lote para que cada alumno solo vea los avisos de su programa y las publicaciones habilitadas para su lote.
- Respeto de los lotes excluidos a nivel publicación, incluso en las búsquedas con `sudo()` del controlador.
- Override de la funcionalidad de compartir posts.
- Estilos SCSS dedicados para el popup.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `irg.forum.notice` (nuevo) | Nuevo | Aviso, foro relacionado, lote, activo, fecha |

## Vistas y UI

- Popup frontend con el aviso de foro.
- Gestión de avisos desde el backend (lista y formulario).

## Notas técnicas

- Requiere `security/ir.model.access.csv` por crear un modelo nuevo.
- Assets JS para la lógica del popup y override de compartir.
- El controlador aplica `_filter_visible_for_user()` sobre las publicaciones candidatas para no depender únicamente de `ir.rule`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_forum_notice_popup \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_forum_notice_popup \
    --stop-after-init --db_host=pgodoo_latest
```
