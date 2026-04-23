# irg_forum_batch_visibility

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `website_forum`, `openeducat_core`

---

## ¿Qué hace este módulo?

Restringe la visibilidad de los foros del campus a grupos concretos de alumnos (lotes/batches). Sin este módulo, todos los foros serían accesibles por cualquier estudiante registrado. Con él, cada foro puede configurarse para que solo lo vean los alumnos pertenecientes a un lote o curso específico.

Además incluye mejoras visuales de interfaz que informan al alumno cuándo un post no puede publicarse (feedback de publicación) y ajustes SCSS para el editor del foro.

## Funcionalidades principales

- Campo de configuración de visibilidad por lote en el modelo del foro.
- Reglas de seguridad para restringir el acceso a foros no permitidos (`security/forum_batch_visibility_rules.xml`).
- Vista de gestión de visibilidad por lote en el backoffice.
- Script JS que muestra feedback al intentar publicar en un foro sin permiso.
- SCSS de foco para el editor del foro.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `forum.forum` | Herencia | Campos de configuración de lotes visibles |

## Vistas y UI

- `views/forum_batch_visibility_views.xml` — formulario de configuración de visibilidad en el backend.
- Assets JS/SCSS para el frontend del foro.

## Notas técnicas

- Las reglas de seguridad se aplican en `security/forum_batch_visibility_rules.xml` usando `ir.rule`.
- Es dependencia obligatoria de `irg_forum_email_notify`, `irg_forum_notice_popup` y `irg_campus_course_forum`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_forum_batch_visibility \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_forum_batch_visibility \
    --stop-after-init --db_host=pgodoo_latest
```
