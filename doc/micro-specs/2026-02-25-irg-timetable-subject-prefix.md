# Micro-spec — IRG Timetable Subject Prefix

## ID
2026-02-25-irg-timetable-subject-prefix

## Objetivo
Mostrar en el horario del portal (`/student/timetable`) el título de asignatura con formato `Código - Nombre` (ej. `PC04 - ...`) para evitar pérdida de prefijos visibles.

## Alcance
- Crear módulo nuevo en `addons-extra/extrairg/` con prefijo `irg_`.
- Sobrescribir endpoint JSON `/get-timetable/data` para usar `subject_id.display_name` en `title`.

## Fuera de alcance
- Cambios de UI en plantilla portal.
- Cambios sobre módulos base existentes.

## Dependencias
- `openeducat_timetable_enterprise`
- `isep_openeducat_custom`

## Criterios de aceptación
1. En el portal timetable el evento muestra `PCxx - Nombre` cuando la asignatura tiene código.
2. El endpoint sigue devolviendo el resto de claves esperadas (`start`, `end`, `faculty`, etc.).
3. Instalación y actualización del módulo sin errores.

## Implementación
1. Crear módulo `irg_timetable_subject_prefix`.
2. Añadir controlador con ruta `/get-timetable/data`.
3. Construir `title` con `session.subject_id.display_name`.
4. Mantener compatibilidad con campos adicionales (`time_url_metting`, `time_url_recoding`) si existen.
