# Changelog - irg_forum_batch_visibility

## 16.0.2.0.0 (2026-05-07)
- **Nueva funcionalidad**: Preselección automática de lotes basada en curso académico
  - Añadido campo `irg_course_id` para seleccionar curso
  - Implementado `@api.onchange` que filtra lotes activos post-Moodle (2025-11-01)
  - Lotes elegibles aparecen marcados automáticamente en el formulario
  - Desplegable restringido a lotes válidos para evitar errores manuales

- **Nueva funcionalidad**: Filtrado inteligente de notificaciones
  - Añadido campo `irg_subject_id` para asignatura específica
  - Override en `create` de posts para suscribir solo alumnos relevantes
  - Exclusión de alumnos que ya aprobaron la asignatura (`op.student.subject` state='pass')
  - Integración con sistema nativo de notificaciones Odoo (email/popup)

- **Mejoras de UX**:
  - Campos con opciones `no_create` y `no_open` para evitar creación accidental
  - Interfaz intuitiva: seleccionar curso → lotes aparecen marcados
  - Idempotencia garantizada con comandos Odoo Many2many

- **Cumplimiento Biblia iRG**:
  - Cero modificación de core Odoo
  - Lógica defensiva con fallbacks
  - Documentación completa en micro-spec 2026-05-07-irg_forum_smart_filtering.md