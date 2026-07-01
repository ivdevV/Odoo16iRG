# Changelog: Habilitar Borrado Individual de Asignaturas en Libreta del Alumno (`irg_gradebook_clear_subjects`)

**Fecha:** 2026-07-01  
**Autor:** Antigravity / Google DeepMind  
**Misión:** `irg_gradebook_individual_delete`

## Descripción del Problema
El módulo `isep_gradebook` define un botón individual para borrar asignaturas (`unlink_subject`) con el icono de la papelera en la pestaña de calificaciones. Sin embargo, este botón no funcionaba en la práctica porque la vista tree One2many de asignaturas (`gradebook_subject_ids`) estaba configurada como de sólo lectura (`readonly`) cuando la libreta del alumno estaba en estado `in_progress` o `done`.

Por lo tanto, la papelera no se mostraba ni era interactiva mientras el alumno cursaba las materias.

## Cambios Introducidos

### Módulo `irg_gradebook_clear_subjects` (v16.0.1.1.0)
- **Vistas XML (`views/app_gradebook_student_views.xml`):**
  - Se modificó la herencia de la vista formulario `app.gradebook.student` para sobrescribir los atributos del elemento `tree` en el campo `gradebook_subject_ids`.
  - Se cambió la regla de sólo lectura de la tabla para que aplique únicamente si `state == 'done'`, liberando el estado `in_progress` para permitir que el botón individual de borrar (`unlink_subject`) funcione.
- **Modelos Python (`models/app_gradebook_subject.py`):**
  - Se creó la extensión del modelo `app.gradebook.subject` heredando de Odoo.
  - Se sobrescribió el método `unlink()` para eliminar en cascada todos los registros de evaluación asociados (`gradebook_result_ids`) cuando se elimine una asignatura de forma individual, evitando inconsistencias o registros huérfanos en la base de datos.
- **Manifiesto y Carga (`__manifest__.py` & `models/__init__.py`):**
  - Se importó el nuevo modelo de asignatura en la inicialización de la carpeta `models/`.
  - Se incrementó la versión a `16.0.1.1.0`.
- **Documentación del Módulo (`doc/modules/extrairg/irg_gradebook_clear_subjects.md`):**
  - Se actualizó el manual técnico para describir la nueva funcionalidad de borrado individual y eliminación en cascada.

## Pruebas Realizadas
- Validación sintáctica exitosa usando `py_compile` en los modelos modificados.
- Validación estructural exitosa con `xml.etree.ElementTree` del archivo de vistas modificado.
