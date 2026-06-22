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

También permite configurar visibilidad granular por publicación. Dentro de un foro visible para varios lotes, cada publicación puede indicar lotes que sí pueden visualizarla y lotes que no pueden visualizarla.

Además incluye mejoras visuales de interfaz que informan al alumno cuándo un post no puede publicarse (feedback de publicación) y ajustes SCSS para el editor del foro.

## Funcionalidades principales

- Campo de configuración de visibilidad por lote en el modelo del foro.
- Campos de visibilidad por lote en publicaciones: lotes que pueden visualizar y lotes que no pueden visualizar.
- Reglas de seguridad para restringir el acceso a foros no permitidos (`security/forum_batch_visibility_rules.xml`).
- Reglas de seguridad para restringir publicaciones no permitidas dentro de foros compartidos.
- Vista de gestión de visibilidad por lote en el backoffice.
- Script JS que muestra feedback al intentar publicar en un foro sin permiso.
- SCSS de foco para el editor del foro.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `forum.forum` | Herencia | Campos de configuración de lotes visibles |
| `forum.post` | Herencia | `visibility_batch_ids`, `excluded_visibility_batch_ids`, helpers de visibilidad por usuario |

## Vistas y UI

- `views/forum_batch_visibility_views.xml` — formulario de configuración de visibilidad en el backend.
- En publicaciones de foro, los campos `Lotes que pueden visualizar` y `Lotes que no pueden visualizar` se muestran en la ficha y en el listado backend.
- Assets JS/SCSS para el frontend del foro.

## Notas técnicas

- Las reglas de seguridad se aplican en `security/forum_batch_visibility_rules.xml` usando `ir.rule`.
- En publicaciones, la exclusión gana siempre frente a la inclusión. Si un usuario pertenece a un lote permitido y a uno excluido, no puede leer la publicación.
- Si una publicación no tiene lotes permitidos ni excluidos, hereda la visibilidad del foro.
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
