# irg_op_course_subjects_manage

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG Developer
**Depende de:** `openeducat_core`

---

## ¿Qué hace este módulo?

Añade la posibilidad de gestionar directamente la lista de asignaturas desde el formulario del curso (`op.course`). En Odoo estándar, las asignaturas se gestionan desde su propio formulario; con este módulo, se puede ver y editar la lista de asignaturas asociadas al curso directamente en el formulario del curso.

## Funcionalidades principales

- Pestaña o lista de asignaturas editable en el formulario del curso.

## Vistas y UI

- `views/op_course_views.xml` — pestaña de asignaturas en el formulario de `op.course`.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_op_course_subjects_manage \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_op_course_subjects_manage \
    --stop-after-init --db_host=pgodoo_latest
```
