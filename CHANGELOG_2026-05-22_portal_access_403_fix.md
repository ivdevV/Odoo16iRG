# Changelog 2026-05-22 — Resolución de Error de Acceso 403 en el Portal del Alumno

## Resumen
Se implementa una solución definitiva para el error `403 Forbidden AccessError` que impedía a los alumnos acceder a su dashboard de portal. Este error se originaba en los campos calculados de progreso (`total_completion_porc` en `op.student` y `completion_porc` en `op.student.course`), los cuales consultaban modelos restringidos (`op.subject`, `app.gradebook.subject`) bajo los permisos del usuario sin privilegios administrativos. La resolución se implementó en un módulo nuevo (`irg_portal_student_fix`) mediante herencia, sin modificar ningún módulo preexistente.

## Cambios por módulo

### [NEW] `addons-extra/extrairg/irg_portal_student_fix` (16.0.1.0.0)
* **Manifiesto e inicialización (`__manifest__.py`, `__init__.py`):**
  - Creación del nuevo módulo personalizado.
  - Dependencias declaradas sobre `isep_student_filter` e `isep_gradebook`.
* **Modelos (`models/op_student.py`):**
  - **Hereda de `op.student`:** Sobreescribe `_compute_total_completion` ejecutando las consultas del progreso total de asignaturas obligatorias y su nota final mediante privilegios administrativos (`sudo()`).
  - **Hereda de `op.student.course`:** Sobreescribe `_compute_advance_search` ejecutando el conteo de asignaturas obligatorias totales de un curso e inscripciones aprobadas mediante privilegios administrativos (`sudo()`).

## Documentación
* Creada la documentación de referencia técnica en [irg_portal_student_fix.md](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/doc/modules/extrairg/irg_portal_student_fix.md).

## Pruebas y Validación Local
Los cambios han sido validados de forma satisfactoria en el entorno Docker local (`odoo16irg_local`) contra la base de datos `test_irg_db`.

### Validación funcional vía Odoo Shell:
Se ejecutó un script de diagnóstico simulando el contexto de seguridad del usuario portal (`saoyara@gmail.com` / UID `90`):
```bash
docker exec -i odoo16irg_local odoo shell -c /etc/odoo/odoo.conf -d test_irg_db < scratch/test_student_compute.py
```

### Resultados de validación:
* **Estado:** Aprobado / Exitoso (Passed)
* **Error 403:** Resuelto.
* **Salida de diagnóstico:**
  - Acceso a `total_completion_porc` como usuario portal: **SUCCESS (0.0%)**
  - Acceso a `completion_porc` de sus cursos asociados como usuario portal: **SUCCESS (0.0%)** para todos los registros del alumno.
