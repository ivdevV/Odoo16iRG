# Plan: Módulo irg_partner_openeducat_info

## Alcance y Clasificación
- **Nivel de Misión**: `light` / `full` (Creación del nuevo módulo `irg_partner_openeducat_info` en `addons-extra/extrairg/`).
- **Capacidad Requerida**: Standard (Estructura de módulo Odoo 16, herencia de modelos res.partner y op.student, y vistas XML de res.partner).

## Criterios de Aceptación
1. **Creación del Módulo**: Crear la carpeta `addons-extra/extrairg/irg_partner_openeducat_info` con la estructura estándar de Odoo (`__manifest__.py`, `__init__.py`, `models/res_partner.py`, `views/res_partner_views.xml`, `tests/test_partner_openeducat_info.py`).
2. **Dependencias**: Depender de `base`, `openeducat_core`, `isep_student_filter`, `isep_student_access`.
3. **Integración en Contactos (`res.partner`)**:
   - Pestaña "Educativo": Muestra Matrícula (`gr_no`), Programa SEP (`sepyc_program`), Estado de Estudiante (`status_student`), Fecha Cierre de Expediente (`file_closing_date`), Progreso Total (`total_completion_porc`), Admisiones (`op_admission_ids`) y Cursos (`op_course_ids`).
   - Pestaña "Acceso": Muestra la fecha de última autenticación (`login_date`) y el historial de accesos (`login_line_ids`).
4. **Comprobación y Verificación**: Comprobar sintaxis Python, cargar/ejecutar pruebas unitarias y verificar la visualización en la ficha de contactos.

## Matriz de Roles
- **Orquestador**: Planificación y control del ciclo de vida.
- **Codificador**: Creación del modelo, vistas y pruebas unitarias.
- **Revisor**: Revisión del código diff y sintaxis XML/Python.
- **Validador**: Ejecución de checks y validación del módulo.
- **Documentador**: Actualización de `execution.md` y `CHANGELOG.md`.

## Fases del Ciclo de Vida
1. **Plan**: `plan.md` e `implementation_plan.md` creados. Esperando confirmación/feedback del usuario.
2. **Implementación**: Creación de los archivos del módulo.
3. **Review de Código**: Inspección de diffs y verificación.
4. **Validación**: Pruebas unitarias e integración local.
5. **Documentación**: Registrar en `execution.md` y `CHANGELOG.md`.
