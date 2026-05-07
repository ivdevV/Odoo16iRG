# Micro-Spec: IRG Forum Smart Filtering (2026-05-07)

## Título
Implementación de preselección automática de lotes y filtrado inteligente de notificaciones en foros académicos

## Resumen
Modificar `irg_forum_batch_visibility` para automatizar la selección de lotes basada en curso académico, fecha de corte Moodle (2025-11-01) y estado activo, además de implementar notificaciones inteligentes que excluyan alumnos que ya aprobaron la asignatura.

## Motivo
- Reducir errores manuales en configuración de visibilidad de foros
- Evitar spam académico notificando solo a alumnos relevantes
- Mantener consistencia con la era post-Moodle (noviembre 2025)
- Optimizar UX para directores de curso

## Alcance exacto
- Modelo `forum.forum`: añadir campo `irg_course_id` y lógica `@api.onchange`
- Vista formulario: insertar campo curso antes de lotes
- Modelo `forum.post`: override `create` para suscripción inteligente
- No modificar core Odoo ni módulos nativos

## Diseño técnico
### Modelo forum.forum
- Campo: `irg_course_id` (Many2one a `op.course`)
- Constante: `MOODLE_CUTOFF = date(2025, 11, 1)`
- Onchange: filtrar lotes con `course_id`, `start_date >= cutoff`, `start_date <= today`, `state = 'active'`
- Comando: `(6, 0, ids)` para autoseleccionar
- Domain: restringir desplegable a lotes elegibles

### Vista
- Herencia: `inherit_id` a `website_forum.view_forum_forum_form`
- XPath: `//field[@name='visibility_batch_ids']` position="before"
- Atributos: `options="{'no_create': True, 'no_open': True}"`

### Modelo forum.post
- Override `create`: identificar lotes del foro
- Buscar estudiantes matriculados (`op.student.course` state='done')
- Filtrar: excluir si `op.student.subject` state='pass' para la asignatura del foro
- Acción: `message_subscribe` con partner_ids filtrados

## Dependencias
- `website_forum`
- `openeducat_core`
- `irg_forum_batch_visibility` (existente)

## Compatibilidad/migración
- Aditivo: no rompe funcionalidad existente
- Idempotente: onchange usa `(6, 0, ids)` sin duplicados
- Fallback: si no hay curso, limpiar lotes

## Casos de prueba
1. Seleccionar curso → lotes elegibles aparecen marcados
2. Cambiar curso → lotes se actualizan sin duplicados
3. Crear post → solo alumnos no aprobados reciben notificación
4. Foro sin curso → comportamiento original

## Rollback
- Desinstalar módulo: vuelve a manual
- Revertir commit: elimina campo y lógica

## Estimación y responsable
- Esfuerzo: 4 horas
- Responsable: Desarrollador senior Odoo 16
- Fecha: 2026-05-07