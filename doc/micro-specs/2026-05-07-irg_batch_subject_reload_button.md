# Boton para recargar asignaturas del lote

## 1. Titulo corto

Boton de recarga de asignaturas en lotes.

## 2. Resumen objetivo

Crear un modulo extra que anada un boton en la pestana "Programar Asignaturas" del formulario de lote para sincronizar manualmente las asignaturas programadas con las asignaturas del curso asociado.

## 3. Motivo / justificacion

El modulo `isep_elearning_custom` autogenera las lineas de `op.subject.to.batch` al crear el lote o cambiar el curso, pero no ofrece una accion explicita para regenerar la lista cuando el curso cambia sus asignaturas despues de existir el lote. La solucion debe implementarse por herencia en un modulo `irg_*`, sin tocar modulos existentes ni core.

## 4. Alcance exacto

- Modelo `op.batch`: nuevo metodo de accion para sincronizar `subject_to_batch_ids` desde `course_id.subject_ids`.
- Vista `op.batch`: boton en la pestana `pro_subject` antes de la tabla `subject_to_batch_ids`.
- Tests: casos de adicion, limpieza de asignaturas ajenas y conservacion de fechas existentes.

No se crean modelos, controladores, assets, crons ni reglas de seguridad nuevas.

## 5. Diseno tecnico

- Modulo nuevo: `irg_batch_subject_reload_button`.
- Hereda `op.batch` mediante `_inherit`.
- Metodo `action_irg_reload_subject_to_batch`:
  - Requiere que el lote tenga `course_id`.
  - Lee `course_id.subject_ids`.
  - Mantiene las lineas ya existentes cuya asignatura sigue perteneciendo al curso.
  - Elimina lineas duplicadas o de asignaturas que ya no pertenecen al curso.
  - Crea lineas faltantes en `op.subject.to.batch`, copiando `code` desde `op.subject.code`.
  - Devuelve una notificacion cliente con el resumen de la sincronizacion.
- Vista XML:
  - Hereda `irg_batch_subject_schedule_manual.view_op_batch_form_subject_schedule_manual`.
  - Inserta un boton `type="object"` antes de `subject_to_batch_ids` en la pagina `pro_subject`.

## 6. Dependencias

`depends`:

- `irg_batch_subject_schedule_manual`

Esta dependencia aporta la vista base heredable, las validaciones de asignaturas por curso y la sincronizacion de codigo en `op.subject.to.batch`.

## 7. Backwards-compatibility / migracion

No requiere migracion de datos. El boton opera bajo demanda y no altera el comportamiento automatico existente al crear lotes o cambiar `course_id`.

## 8. Casos de prueba / criterios de aceptacion

- Al pulsar el boton, se crean las lineas que falten para todas las asignaturas del curso.
- Las lineas existentes para asignaturas del curso conservan sus fechas.
- Las lineas duplicadas o ajenas al curso se eliminan durante la sincronizacion.
- Si el lote no tiene curso, se muestra un `UserError` traducible.
- El boton aparece en la pestana "Programar Asignaturas" del formulario de lote.

## 9. Rollback plan

Desinstalar el modulo:

```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u base --stop-after-init --db_host=pgodoo_latest
```

O revertir el commit que introduce `irg_batch_subject_reload_button` y actualizar la lista de aplicaciones.

## 10. Estimacion y responsable

- Estimacion: 1 hora.
- Responsable: IRG / Copilot.