# Plan - Eliminar asignatura individualmente en app.gradebook

Permitir la eliminación individual de asignaturas en el libro de calificaciones del estudiante (`app.gradebook.student`) desde la vista tree, corrigiendo la contradicción de sólo lectura que impedía usar el botón individual de papelera en estado `in_progress`.

## Justificación y Clasificación de Complejidad

- **Tier de Complejidad:** `standard`
- **Justificación:** Afecta a 2 archivos dentro de un módulo personalizado local (`irg_gradebook_clear_subjects`), modificando la vista heredada mediante XPath y extendiendo la lógica del modelo de asignaturas (`app.gradebook.subject`) para mantener la integridad referencial (eliminación en cascada de evaluaciones asociadas).
- **Modelo:** Gemini 3.5 Flash (Tier Standard).

## Cambios Propuestos

### Módulo `irg_gradebook_clear_subjects`

#### [MODIFY] [app_gradebook_student_views.xml](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_gradebook_clear_subjects/views/app_gradebook_student_views.xml)
- Modificar el atributo `readonly` en el campo `gradebook_subject_ids` (el tree) para que sea sólo de lectura cuando el estado sea `done`, en lugar de `done` o `in_progress`. Esto permitirá interactuar con el botón `unlink_subject` cuando la libreta esté en estado `in_progress`.
- Asegurar que los campos individuales del tree sigan siendo de sólo lectura (opcional, dado que son campos `compute` almacenados no tienen edición manual habilitada).

#### [NEW] [app_gradebook_subject.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_gradebook_clear_subjects/models/app_gradebook_subject.py)
- Crear el modelo extendido para `app.gradebook.subject`.
- Sobrescribir el método `unlink()` para que elimine en cascada sus evaluaciones asociadas (`gradebook_result_ids`), previniendo registros huérfanos o errores de restricción.

#### [MODIFY] [__init__.py](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_gradebook_clear_subjects/models/__init__.py)
- Importar el nuevo modelo `app_gradebook_subject`.

## Plan de Verificación

### Pruebas de Sintaxis y Linting
- Ejecutar un chequeo de sintaxis de python (`python3 -m py_compile`) en los archivos nuevos/modificados de python.

### Verificación de Vistas (XML)
- Validar el formato XML del archivo de vistas modificado.
