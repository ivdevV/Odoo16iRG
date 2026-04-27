# irg_op_subject_multi_course

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG Developer
**Depende de:** `openeducat_core_enterprise`

---

## ¿Qué hace este módulo?

Permite asociar una misma asignatura (`op.subject`) a múltiples cursos de forma segura, sin romper las relaciones existentes ni los filtros por curso. En OpenEduCat estándar, la relación es uno-a-uno (una asignatura pertenece a un único curso).

## Funcionalidades principales

- Relación Many2many entre `op.subject` y `op.course`.
- Gestión de la lista de cursos desde el formulario de la asignatura.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.subject` | Herencia | Relación many2many a `op.course` |

## Vistas y UI

- `views/op_subject_views.xml` — lista de cursos en el formulario de la asignatura.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_op_subject_multi_course \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_op_subject_multi_course \
    --stop-after-init --db_host=pgodoo_latest
```
