# irg_campus_course_forum

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `isep_website_custom`, `isep_website_custom_inh`, `openeducat_lms_forum`, `irg_forum_batch_visibility`

---

## ¿Qué hace este módulo?

Integra una sección de foro del curso en el panel del campus del alumno. Muestra el foro específico de cada programa/curso dentro del perfil del usuario en el campus, permitiendo que los alumnos accedan al foro de su clase directamente desde su panel de inicio.

## Funcionalidades principales

- Sección "Foro del Curso" en el panel de perfil del campus del alumno.
- Enlace directo al foro filtrado por lote (batch) del estudiante.
- Integración con `irg_forum_batch_visibility` para mostrar solo los foros del lote activo.

## Vistas y UI

- `views/user_profile_course_forum.xml` — sección de foro en el perfil de curso del campus.

## Notas técnicas

- Dependencia transitiva de `openeducat_lms_forum` (OpenEduCat Enterprise) para la integración LMS-foro.
- Es dependencia de `irg_forum_notice_popup`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_campus_course_forum \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_campus_course_forum \
    --stop-after-init --db_host=pgodoo_latest
```
