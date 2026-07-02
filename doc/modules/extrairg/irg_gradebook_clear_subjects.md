# irg_gradebook_clear_subjects

**Categoría:** extrairg  
**Versión:** 16.0.1.1.0  
**Licencia:** LGPL-3  
**Instalable:** Sí  
**Autor:** IRG  
**Depende de:** `isep_gradebook`

---

## ¿Qué hace este módulo?

Añade herramientas de borrado en la libreta del alumno (`app.gradebook.student`) tanto para borrar todas las asignaturas de golpe como para permitir la eliminación individual de una materia específica en estado *En proceso*.

## Funcionalidades principales

- **Borrar todas las asignaturas (Cabecera):** Botón "Borrar Asignaturas" en la cabecera del formulario de la libreta, disponible en estado `in_progress`. Elimina todas las materias de la libreta junto con sus calificaciones asociadas.
- **Borrado individual de asignaturas (Línea):** Habilita el botón nativo de papelera (`unlink_subject`) al final de cada línea de asignatura de la libreta del alumno en estado `in_progress`. Esto se logra redefiniendo el atributo `readonly` del tree de One2many para que sólo se aplique en estado `done`.
- **Integridad referencial (Borrado en cascada):** Sobrescribe el método `unlink()` en `app.gradebook.subject` para asegurar que, al eliminar una asignatura de manera individual, sus evaluaciones correspondientes (`gradebook_result_ids`) también se eliminen automáticamente de la base de datos.

## Vistas y UI

- `views/app_gradebook_student_views.xml` — Añade el botón de borrado masivo en la cabecera y redefine el `readonly` del tree de asignaturas.

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
