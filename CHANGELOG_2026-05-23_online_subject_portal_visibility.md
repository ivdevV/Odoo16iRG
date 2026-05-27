# Changelog - irg_online_subject_portal_visibility

Historial de cambios realizados en el módulo de Visibilidad de Asignaturas Online en Portal.

## [16.0.1.1.0] - 2026-05-23

### Modificaciones
- **Dependencias**: Se añade `'irg_course_convocatorias_v2'` a la lista de dependencias en `__manifest__.py`.
- **Modelo `slide.channel`**: Se hereda del modelo y se sobrescribe `_irg_is_partner_online_student_for_channel(self, partner)`. Esta sobrescritura permite realizar comprobaciones específicas para estudiantes online (usando `admission.due_date` individual en lugar del `batch.end_date` global del lote), resolviendo el problema por el cual los alumnos online activos veían todas las asignaturas por no ser identificados correctamente.
- **Controlador `OnlineSubjectVisibilitySlides`**: Se hereda ahora de `CourseConvocatoriasSlides` (en lugar de `SubjectVisibilitySlides`). De esta manera se preservan los redireccionamientos a canales clon y HomeClass definidos en `irg_course_convocatorias_v2` antes de aplicar la restricción de visibilidad. En caso de acceso válido a una asignatura, se puentea a `WebsiteSlides.channel` directamente para evitar la validación por lote obsoleta de `CustomWebsiteSlides`.
- **Tests**: Se añade el caso de prueba `test_clone_redirection_preservation` a `TestOnlineSubjectPortalVisibility` para asegurar que las redirecciones automáticas a canales clon preserven su funcionalidad con la nueva jerarquía de controladores.

## [16.0.1.0.0] - 2026-05-23

### Características
- **Creación inicial del módulo**: Implementación de restricciones de acceso y visibilidad en portal para asignaturas online según fecha de vencimiento individual (`due_date`) y calendario de apertura individual (`irg_get_visible_online_subjects_for_date`).
- **Controlador de Aviso**: Adición de `/warning/online_admission/<id>` para informar sobre el vencimiento del curso.
- **Plantilla QWeb**: Creación de la vista `template_online_admission_expired`.
- **Tests**: Implementación de 4 casos de prueba iniciales.
