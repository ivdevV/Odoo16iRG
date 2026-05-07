# irg_batch_subject_schedule_manual

## 1. Titulo corto
Asignaturas manuales en lotes academicos.

## 2. Resumen objetivo
Permitir anadir asignaturas manualmente en la tabla **Programar Asignaturas** del formulario de lotes (`op.batch`). La asignatura seleccionada debe copiar su codigo automaticamente y conservar la edicion de las fechas de inicio y fin.

## 3. Motivo / justificacion
La tabla actual existe en `isep_elearning_custom`, pero el campo `subject_id` se muestra como solo lectura, por lo que no permite crear nuevas lineas utiles desde la interfaz. La solucion se implementa como modulo extra para no modificar OpenEduCat ni el modulo UISep existente, respetando la arquitectura de herencia del proyecto.

## 4. Alcance exacto
- Modelos heredados: `op.batch` y `op.subject.to.batch`.
- Vista heredada: formulario de `op.batch`, extension de la pestaña **Programar Asignaturas**.
- No se crean nuevos modelos, controladores, assets ni reportes.
- No se modifica codigo nativo ni modulos ya existentes.

## 5. Diseno tecnico
- Crear modulo `irg_batch_subject_schedule_manual` en `addons-extra/extrairg/`.
- Heredar `op.subject.to.batch` para:
  - Rellenar `code` desde `subject_id.code` en onchange, create y write.
  - Bloquear asignaturas que no pertenezcan a `batch_id.course_id.subject_ids`.
  - Bloquear duplicados por combinacion `batch_id` + `subject_id`.
- Heredar `op.batch` para exponer `irg_course_subject_ids`, un campo relacionado invisible con las asignaturas del curso, usado por el dominio de la tabla.
- En cambios de `course_id`, preservar la autopoblacion existente de `isep_elearning_custom` usando un contexto interno que evita validar contra el curso antiguo mientras el modulo base recrea las lineas.
- Heredar la vista `isep_elearning_custom.custom_op_batch_subject_form` y modificar el campo `subject_id` dentro de `subject_to_batch_ids` para hacerlo editable, limitado a las asignaturas del curso del lote y sin creacion rapida desde el desplegable.
- Mantener `code` como solo lectura y `date_from` / `date_to` editables.

## 6. Dependencias
- `isep_elearning_custom`: define `op.subject.to.batch`, el One2many `subject_to_batch_ids` y la pestaña **Programar Asignaturas**.

## 7. Backwards-compatibility / migracion
El modulo no altera datos existentes. Las lineas ya creadas continuan funcionando y las fechas existentes se conservan. La nueva validacion evita nuevas inconsistencias, pero no ejecuta migraciones sobre historico. El flujo existente que recrea lineas al cambiar el curso del lote se mantiene compatible.

## 8. Casos de prueba / criterios de aceptacion
- Se puede pulsar **Agregar linea** y seleccionar una asignatura del curso del lote.
- El campo `code` se rellena automaticamente con el codigo de la asignatura.
- `date_from` y `date_to` siguen editables.
- No se puede guardar una asignatura que no pertenezca al curso del lote.
- No se puede repetir la misma asignatura en el mismo lote.
- La instalacion/actualizacion del modulo no produce errores XML ni Python.

## 9. Rollback plan
```bash
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u isep_elearning_custom \
    --stop-after-init --db_host=pgodoo_latest
```

Si el modulo estuviera instalado, desinstalar `irg_batch_subject_schedule_manual` desde Apps o con el flujo administrativo habitual y actualizar `isep_elearning_custom` si fuera necesario.

## 10. Estimacion y responsable
- Estimacion: 0.5 jornada.
- Responsable: iRG / GitHub Copilot.