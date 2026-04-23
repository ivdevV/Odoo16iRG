# irg_gradebook_clear_subjects

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `isep_gradebook`

---

## ¿Qué hace este módulo?

Añade un botón en el formulario de la libreta del alumno (`app.gradebook.student`) para eliminar todas las asignaturas de la libreta de una sola vez. Útil para resetear la libreta antes de recargar asignaturas.

## Funcionalidades principales

- Botón "Borrar todas las asignaturas" en el formulario de la libreta.
- Acción de servidor que elimina todos los registros de asignatura asociados.

## Vistas y UI

- `views/app_gradebook_student_views.xml` — botón añadido en el formulario de la libreta.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_gradebook_clear_subjects \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_gradebook_clear_subjects \
    --stop-after-init --db_host=pgodoo_latest
```
