# Changelog - 2026-06-01 - irg_admission_class_start_date

## Added

- Nuevo modulo `irg_admission_class_start_date` para anadir `Fecha de inicio de clases` en `op.admission`.
- Campo tecnico `irg_class_start_date` de tipo fecha, no copiable y readonly en admisiones `done`.
- Herencia del formulario `openeducat_admission.view_op_admission_form` para mostrar el campo despues de `Due Date`.
- Micro-spec y documentacion tecnica del modulo.

## Changed

- El campo `irg_class_start_date` queda editable desde la admision sin bloqueo especifico por estado.
- Documentado que la fecha de inicio de clases es independiente del lote y no se sincroniza con `batch_id`.

## Notes

- El campo se muestra solo en el formulario de admision.
- No se anaden modelos, ACLs, automatizaciones, listados ni filtros nuevos.