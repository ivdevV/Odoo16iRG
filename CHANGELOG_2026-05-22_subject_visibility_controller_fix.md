# Changelog - 2026-05-22

## Corrección del Controlador de Visibilidad de Asignaturas e Integración de Apertura Online

**Fecha:** 2026-05-22

### Descripción
Resuelve los fallos en las comprobaciones de acceso para asignaturas restringidas mediante URLs directas de canales de diapositivas (`/slides/<channel>`). Filtra las admisiones por los cursos de la asignatura para evitar el desbordamiento de acceso entre cursos (cross-course bleed) y verifica si la asignatura está abierta para admisiones de apertura online. En caso contrario, redirige a la página de advertencia.

### Validación
- **Pruebas unitarias de Odoo**: 16 pruebas ejecutadas y superadas con éxito.
- **Simulación en Odoo shell**: Redirección correcta a `/warning/subject-visibility/35` para el partner `201` en el canal `35`.
