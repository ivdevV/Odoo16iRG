# irg_batch_subject_reload_button

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** IRG
**Depende de:** `irg_batch_subject_schedule_manual`

---

## ¿Qué hace este módulo?

Añade un botón de recarga en la pestaña **Programar Asignaturas** del formulario de lote (`op.batch`). Su objetivo es sincronizar las líneas de planificación `op.subject.to.batch` con la lista oficial de asignaturas configurada en el curso del lote (`course_id.subject_ids`).

El módulo resuelve el caso en el que un curso cambia sus asignaturas después de haber creado o editado un lote. En lugar de reconstruir manualmente la planificación, el usuario puede pulsar **Recargar asignaturas** para añadir las asignaturas que faltan, eliminar líneas duplicadas o ajenas al curso y conservar las fechas ya programadas de las asignaturas que siguen siendo válidas.

## Funcionalidades principales

- Botón **Recargar asignaturas** en la pestaña **Programar Asignaturas** del formulario de `op.batch`.
- Sincronización de `subject_to_batch_ids` a partir de `course_id.subject_ids`.
- Creación automática de líneas `op.subject.to.batch` para asignaturas del curso que aún no están planificadas en el lote.
- Conservación de `date_from` y `date_to` en líneas existentes cuando la asignatura sigue perteneciendo al curso.
- Eliminación de líneas duplicadas, líneas sin asignatura y líneas cuya asignatura ya no pertenece al curso del lote.
- Validación de uso: si el lote no tiene curso asignado, se muestra un error funcional.
- Notificación de éxito con el número de asignaturas añadidas y líneas eliminadas, seguida de recarga de la vista.

## Modelos

| Modelo | Tipo | Campos principales |
|--------|------|--------------------|
| `op.batch` | Herencia | Usa `course_id` y `subject_to_batch_ids`; añade el método `action_irg_reload_subject_to_batch()` |
| `op.subject.to.batch` | Uso indirecto | `batch_id`, `subject_id`, `code`, `date_from`, `date_to` |

## Vistas y UI

- `views/op_batch_views.xml` hereda `irg_batch_subject_schedule_manual.view_op_batch_form_subject_schedule_manual`.
- Inserta el botón **Recargar asignaturas** antes del campo `subject_to_batch_ids` dentro de la página `pro_subject`, correspondiente a la pestaña **Programar Asignaturas**.
- El botón ejecuta el método Python `action_irg_reload_subject_to_batch()` mediante `type="object"`.
- Incluye icono `fa-refresh`, estilo `btn-secondary` y confirmación previa para advertir que se sincronizarán las asignaturas del lote con el curso actual.

## Tests

El módulo incluye tests transaccionales en `tests/test_batch_subject_reload.py`, etiquetados como `post_install` y `-at_install`.

Casos cubiertos:

- Añade asignaturas faltantes del curso al lote.
- Conserva fechas existentes (`date_from`, `date_to`) para asignaturas válidas.
- Elimina líneas duplicadas y asignaturas ajenas al curso.
- Lanza `UserError` cuando se intenta recargar un lote sin curso asignado.

## Dependencias externas

- `irg_batch_subject_schedule_manual`: aporta la vista base de programación manual de asignaturas del lote y el modelo/líneas `op.subject.to.batch` que este módulo sincroniza.

## Notas técnicas

- No crea modelos nuevos ni requiere `security/ir.model.access.csv` propio.
- No define controladores HTTP, rutas públicas ni endpoints.
- No usa `sudo()` ni SQL raw.
- El método trabaja sobre un único lote mediante `ensure_one()`.
- La sincronización toma como fuente de verdad `course_id.subject_ids`.
- Para evitar pérdida de planificación, las líneas existentes se mantienen cuando su `subject_id` pertenece al curso y no están duplicadas; por tanto, sus fechas se conservan.
- Las nuevas líneas se crean con `batch_id`, `subject_id` y `code` heredado desde la asignatura.
- El resultado de la acción es una notificación `display_notification` y una recarga de cliente (`tag: reload`).

## Guía de operación

1. Abrir el lote académico (`op.batch`) que se desea revisar.
2. Verificar que el campo **Curso** está informado.
3. Entrar en la pestaña **Programar Asignaturas**.
4. Pulsar **Recargar asignaturas**.
5. Confirmar la acción cuando Odoo muestre el aviso.
6. Revisar la notificación de resultado y comprobar la lista actualizada.

Después de ejecutar la recarga, las asignaturas del lote quedan alineadas con el curso actual. Las fechas ya configuradas se mantienen para las asignaturas que siguen siendo válidas; solo se añaden las asignaturas faltantes y se eliminan líneas duplicadas o ajenas al curso.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_batch_subject_reload_button \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_batch_subject_reload_button \
    --stop-after-init --db_host=pgodoo_latest
```
