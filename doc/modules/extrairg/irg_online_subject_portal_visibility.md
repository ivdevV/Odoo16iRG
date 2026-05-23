# irg_online_subject_portal_visibility

**Categoría:** extrairg
**Versión:** 16.0.1.0.0
**Licencia:** LGPL-3
**Instalable:** Sí
**Autor:** iRG Developer
**Depende de:** `isep_elearning_custom`, `irg_op_subject_visibility`, `irg_online_subject_opening`

---

## ¿Qué hace este módulo?

Extiende el control de acceso y visibilidad de asignaturas en el portal eLearning para dar soporte a cursos en modalidad online con calendario de ventanas individuales. Bypassa las restricciones globales obsoletas por lote si el alumno tiene una admisión online válida, y aplica la restricción de vencimiento basada en la fecha de vencimiento (`due_date`) de la admisión online individual.

## Funcionalidades principales

- Sobrescribe la ruta de canales de eLearning `/slides/<model("slide.channel"):channel>` para bypassear la restricción global obsoleta por lote cuando hay un curso online activo.
- Restringe el acceso a canales de eLearning según la fecha de vencimiento (`due_date`) y la ventana de apertura individual (`irg_get_visible_online_subjects_for_date`) para alumnos en modalidad online.
- Avisa al alumno cuando su matrícula online ha expirado a través de una página de aviso personalizada `/warning/online_admission/<int:admission_id>` con controles de seguridad.

## Modelos y Controladores

### Controladores

| Controlador | Métodos clave | Descripción |
|-------------|---------------|-------------|
| `OnlineSubjectVisibilitySlides` | `channel`, `_check_subject_visibility` | Sobrescribe las rutas de canales de eLearning y el método de comprobación de visibilidad de asignaturas. |
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

## Changelog

### [16.0.1.0.0] - 2026-05-23
- Creación del módulo y primera release.
