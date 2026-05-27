# irg_online_subject_portal_visibility

**Categoría:** extrairg
**Versión:** 16.0.1.1.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG Developer
**Depende de:** `isep_elearning_custom`, `irg_op_subject_visibility`, `irg_online_subject_opening`, `irg_course_convocatorias_v2`


---

## ¿Qué hace este módulo?

Extiende el control de acceso y visibilidad de asignaturas en el portal eLearning para dar soporte a cursos en modalidad online con calendario de ventanas individuales. Bypassa las restricciones globales obsoletas por lote si el alumno tiene una admisión online válida, y aplica la restricción de vencimiento basada en la fecha de vencimiento (`due_date`) de la admisión online individual.

## Funcionalidades principales

- Sobrescribe la ruta de canales de eLearning `/slides/<model("slide.channel"):channel>` para bypassear la restricción global obsoleta por lote cuando hay un curso online activo.
- Oculta del portal las asignaturas online cuyas fechas de inicio (apertura) sean futuras (posteriores a la fecha actual), mostrando únicamente aquellas cuya ventana de apertura y cierre comprenda la fecha actual.
- Restringe el acceso a canales de eLearning según la fecha de vencimiento (`due_date`) y la ventana de apertura individual (`irg_get_visible_online_subjects_for_date`) para alumnos en modalidad online.
- Avisa al alumno cuando su matrícula online ha expirado a través de una página de aviso personalizada `/warning/online_admission/<int:admission_id>` con controles de seguridad.

## Modelos y Controladores

### Modelos

- `slide.channel`: Sobrescribe `_irg_is_partner_online_student_for_channel` para verificar si un estudiante online está activo usando `admission.due_date` en lugar de la fecha de finalización global del lote (`batch.end_date`).

### Controladores

| Controlador / Clase | Métodos clave | Descripción |
|-------------|---------------|-------------|
| `OnlineSubjectVisibilitySlides` | `channel`, `_check_subject_visibility` | Sobrescribe las rutas de canales de eLearning heredando de `CourseConvocatoriasSlides`. Preserva las redirecciones a clones online y realiza la validación de visibilidad bypassando `CustomWebsiteSlides` para evitar el bloqueo por fecha global. |
| `OnlineWarningAdmissionController` | `warning_online_admission` (ruta `/warning/online_admission/<id>`) | Renderiza la pantalla de aviso de admisión expirada con controles de seguridad. |

## Vistas y UI

- `templates/portal_online_visibility_tmpl.xml` — Plantilla QWeb `template_online_admission_expired` para el aviso de vencimiento de matrícula.

## Instalación / Actualización

```bash
# Instalar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -i irg_online_subject_portal_visibility \
    --stop-after-init --db_host=pgodoo_latest

# Actualizar
docker exec odoo_latest odoo -c /etc/odoo/odoo.conf \
    -d <dbname> -u irg_online_subject_portal_visibility \
    --stop-after-init --db_host=pgodoo_latest
```

## Pruebas realizadas (Validación)

Se ha verificado el correcto funcionamiento del módulo mediante la clase de pruebas `TestOnlineSubjectPortalVisibility`, la cual incluye los siguientes casos de prueba:

- `test_active_online_student_access`: Verifica que un alumno con una admisión online activa y válida pueda acceder correctamente a los contenidos de su asignatura en el portal.
- `test_expired_online_student_blocked`: Valida que un alumno cuya admisión online ha superado su fecha de vencimiento (`due_date`) sea redirigido y bloqueado en el portal.
- `test_mixed_admissions_access`: Comprueba la gestión del acceso cuando un estudiante posee múltiples admisiones simultáneas (por ejemplo, admisiones activas y expiradas).
- `test_standard_admissions`: Asegura que el flujo estándar para admisiones tradicionales y por lotes siga operando normalmente sin interferencias.
- `test_clone_redirection_preservation`: Valida que los estudiantes con modalidad online activa que accedan al canal principal (HomeClass) sean redirigidos correctamente al canal clon correspondiente para online.

## Changelog

### [16.0.1.1.0] - 2026-05-23
- Se agrega dependencia de `irg_course_convocatorias_v2`.
- Se hereda de `slide.channel` para sobrescribir `_irg_is_partner_online_student_for_channel` y evaluar el vencimiento online de forma individual (`admission.due_date`) en lugar de lote (`batch.end_date`).
- Se reestructura el controlador `OnlineSubjectVisibilitySlides` heredando de `CourseConvocatoriasSlides` para preservar redireccionamientos a clones antes de aplicar restricciones de visibilidad de asignaturas online.
- Se añade caso de prueba `test_clone_redirection_preservation`.

### [16.0.1.0.0] - 2026-05-23
- Creación del módulo y primera release.
