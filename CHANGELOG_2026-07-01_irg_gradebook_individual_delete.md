# Changelog: Habilitar Borrado Individual de Asignaturas en Libreta del Alumno (`irg_gradebook_clear_subjects`)

**Fecha:** 2026-07-01  
**Autor:** Antigravity / Google DeepMind  
**Misión:** `irg_gradebook_individual_delete`

## Descripción del Problema
El módulo `isep_gradebook` define un botón individual para borrar asignaturas (`unlink_subject`) con el icono de la papelera en la pestaña de calificaciones. Sin embargo, este botón no funcionaba en la práctica porque la vista tree One2many de asignaturas (`gradebook_subject_ids`) estaba configurada como de sólo lectura (`readonly`) cuando la libreta del alumno estaba en estado `in_progress` o `done`.

Adicionalmente, se detectó que al remover el `readonly` del tree, el botón seguía sin mostrarse en el cliente web debido a que su regla de invisibilidad original `attrs="{'invisible': [('state', 'in', ('done','draft'))]}"` dependía de un estado computado a nivel de línea que podía no cargarse bien en el cliente web en el VPS o estar vacío, ocultando por completo la papelera.

## Cambios Introducidos

### Módulo `irg_gradebook_clear_subjects` (v16.0.1.1.0)
- **Vistas XML (`views/app_gradebook_student_views.xml`):**
  - Se modificó la herencia de la vista formulario `app.gradebook.student` para sobrescribir los atributos del elemento `tree` en el campo `gradebook_subject_ids`.
  - Se cambió la regla de sólo lectura de la tabla para que aplique únicamente si `state == 'done'`, liberando el estado `in_progress`.
  - Se reemplazó por completo la definición del botón de la papelera (`unlink_subject`) para remover cualquier atributo `attrs` de invisibilidad. Dado que el propio `readonly` del tree en estado `done` desactiva/oculta los botones interactivos automáticamente, las reglas de invisibilidad en el botón del tree eran redundantes y propensas a fallos en el frontend por desincronización de caché.
- **Modelos Python (`models/app_gradebook_subject.py`):**
  - Se creó la extensión del modelo `app.gradebook.subject` heredando de Odoo.
  - Se sobrescribió el método `unlink()` para:
    1. Impedir de forma segura que se eliminen asignaturas de libretas finalizadas (`state == 'done'`), arrojando un error de usuario.
    2. Eliminar en cascada todos los registros de evaluación asociados (`gradebook_result_ids`) cuando se elimine una asignatura de forma individual, evitando inconsistencias o registros huérfanos en la base de datos.
- **Manifiesto y Carga (`__manifest__.py` & `models/__init__.py`):**
  - Se importó el nuevo modelo de asignatura en la inicialización de la carpeta `models/`.
  - Se incrementó la versión a `16.0.1.1.0`.
- **Documentación del Módulo (`doc/modules/extrairg/irg_gradebook_clear_subjects.md`):**
  - Se actualizó el manual técnico para describir la nueva funcionalidad de borrado individual y eliminación en cascada.

## Pruebas Realizadas
- Validación sintáctica exitosa usando `py_compile` en los modelos modificados.
- Validación estructural exitosa con `xml.etree.ElementTree` del archivo de vistas modificado.
