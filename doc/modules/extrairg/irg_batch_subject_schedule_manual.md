# irg_batch_subject_schedule_manual

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `isep_elearning_custom`

---

## ¿Qué hace este módulo?

Permite programar manualmente las asignaturas de un lote (`op.batch`) desde el formulario del propio lote. La edición queda controlada para que el usuario solo pueda seleccionar asignaturas que pertenecen al curso asociado al lote, evitando errores habituales al configurar calendarios académicos o planificaciones por cohorte.

El módulo no crea modelos nuevos ni cambia el flujo general de OpenEduCat/ISEP. Extiende los modelos existentes para abrir la edición del campo de asignatura en la tabla de planificación, mantener sincronizado el código de la asignatura y validar que no se programen asignaturas incorrectas o duplicadas dentro del mismo lote.

## Funcionalidades principales

- Habilita la selección manual de `subject_id` en las líneas de asignaturas del lote.
- Limita el selector a las asignaturas del curso asociado al lote.
- Evita la creación rápida de asignaturas desde esa tabla para mantener la planificación controlada.
- Sincroniza automáticamente el campo `code` con el código de la asignatura seleccionada.
- Impide asignar al lote una asignatura que no pertenece a su curso.
- Impide duplicar la misma asignatura dentro de un mismo lote.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.batch` | Herencia | `irg_course_subject_ids` como Many2many relacionado a `course_id.subject_ids`; preserva la recreación automática de líneas al cambiar `course_id` |
| `op.subject.to.batch` | Herencia | Sin campos nuevos; autocompleta `code` y añade validaciones sobre `batch_id` y `subject_id` |

## Vistas y UI

- `views/op_batch_views.xml` hereda `isep_elearning_custom.custom_op_batch_subject_form`.
- Inserta el campo técnico invisible `irg_course_subject_ids` antes de `subject_to_batch_ids` para poder usarlo como dominio en la vista.
- En la pestaña `pro_subject`, deja editable el campo `subject_id` dentro del árbol de `subject_to_batch_ids`.
- Aplica el dominio `[('id', 'in', parent.irg_course_subject_ids)]` para mostrar solo asignaturas del curso del lote.
- Configura `subject_id` con `no_create` y `no_create_edit` para evitar altas manuales de asignaturas desde la planificación.
- Mantiene `code` como campo de solo lectura en la tabla, ya que su valor se deriva de la asignatura seleccionada.

## Tests

El módulo incluye pruebas transaccionales en `tests/test_subject_to_batch_manual.py`, etiquetadas como `post_install` y `-at_install`.

Casos cubiertos:

- Al crear una línea de `op.subject.to.batch`, el código se copia desde la asignatura y se respetan las fechas configuradas.
- Al cambiar la asignatura de una línea existente, el código se actualiza con el de la nueva asignatura.
- No se permite programar una asignatura que no pertenece al curso del lote.
- No se permite duplicar la misma asignatura en el mismo lote.

## Dependencias externas

- `isep_elearning_custom`: aporta la vista `custom_op_batch_subject_form` heredada y el contexto funcional de planificación de asignaturas por lote.

## Notas técnicas

- No añade modelos nuevos, por lo que no requiere `security/ir.model.access.csv` propio.
- No define controladores HTTP, crons, acciones de servidor ni assets frontend/backend.
- Las validaciones se implementan con `@api.constrains` sobre `batch_id` y `subject_id`.
- La sincronización del código se aplica en `onchange`, `create` y `write`, por lo que cubre tanto edición desde formulario como operaciones ORM.
- Al cambiar el curso de un lote, el módulo mantiene compatible la autopoblación de líneas de `isep_elearning_custom`, que recrea las asignaturas antes de completar el `write` del lote.
- Los mensajes de validación están envueltos con `_()` para traducción.
- No utiliza `sudo()` ni SQL directo.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_batch_subject_schedule_manual \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_batch_subject_schedule_manual \
    --stop-after-init --db_host=pgodoo_latest
```

## Operación

Después de instalar o actualizar el módulo, la gestión manual se realiza desde el formulario del lote, en la pestaña de asignaturas. El operador debe seleccionar únicamente asignaturas disponibles en el curso del lote; si intenta guardar una asignatura ajena al curso o repetir una ya programada, Odoo mostrará un error de validación.

Para ejecutar las pruebas del módulo en una base local:

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_batch_subject_schedule_manual \
    --test-tags /irg_batch_subject_schedule_manual \
    --stop-after-init --db_host=pgodoo_latest
```