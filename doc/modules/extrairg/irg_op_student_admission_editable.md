# irg_op_student_admission_editable

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `openeducat_core`, `openeducat_admission`, `isep_student_filter`, `isep_gradebook`

---

## ¿Qué hace este módulo?

Hace editable el popup de admisión en el formulario del estudiante y muestra los promedios de notas de la libreta. Sin este módulo, los campos de admisión en la ficha del alumno son de solo lectura. Con él, los administradores pueden editar campos clave (fecha, curso, lote, fecha de vencimiento, estado) directamente desde la ficha del alumno.

## Funcionalidades principales

- Popup de admisión editable en el formulario de `op.student`.
- Edición de: fecha, curso, lote, fecha de vencimiento y estado de la admisión.
- Vista de asignaturas de libreta con promedios de notas (solo lectura).
- Campo One2many de asignaturas de gradebook en `op.admission`.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.student` | Herencia | Vista editable del popup de admisión |
| `op.admission` | Herencia | Campo One2many de asignaturas de libreta |

## Vistas y UI

- `views/op_student_view.xml` — override del popup de admisión en el formulario del alumno.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_op_student_admission_editable \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_op_student_admission_editable \
    --stop-after-init --db_host=pgodoo_latest
```
