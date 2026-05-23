# Changelog - Visibilidad de Asignaturas Online en Portal

**Fecha:** 2026-05-23
**Módulo afectado:** `irg_online_subject_portal_visibility` [NUEVO]

## Descripción del Problema
El acceso a los canales de eLearning del portal (`/slides/...`) estaba bloqueado de manera global para alumnos con asignaturas online si tenían cualquier otra admisión expirada en su historial, debido a que el controlador original de `isep_elearning_custom` comprobaba de manera global el campo `batch_id.end_date` sin considerar:
1. Si la admisión actual era online y por tanto no sujeta a restricciones de lote grupal.
2. La fecha de vencimiento individual de la matrícula online (`due_date`).

## Cambios Realizados
1. **Nuevo módulo `irg_online_subject_portal_visibility`**:
   - Creado en la ruta `/addons-extra/extrairg/irg_online_subject_portal_visibility`.
2. **Controlador del Portal (`controllers/main.py`)**:
   - Sobrescribe la ruta `/slides/<model("slide.channel"):channel>` y sus variantes.
   - Aplica el control de ventanas de apertura individual (`irg_get_visible_online_subjects_for_date`) para alumnos en asignaturas online.
   - Aplica control de expiración individual basado en `admission.due_date` para matrículas online.
   - **Bypass**: Si la admisión online es válida y activa, puentea el control global de `CustomWebsiteSlides` llamando directamente a `WebsiteSlides.channel(...)`.
   - Implementa `/warning/online_admission/<int:admission_id>` para redireccionar y mostrar el aviso personalizado de matrícula online expirada.
3. **Vistas y UI (`templates/portal_online_visibility_tmpl.xml`)**:
   - Agrega la plantilla `template_online_admission_expired` para renderizar el aviso con información detallada de la matrícula.

## Pruebas de Validación
Se han implementado y ejecutado pruebas unitarias e integrales en `tests/test_online_subject_portal_visibility.py` logrando un 100% de éxito (0 fallos, 0 errores) en los siguientes escenarios:
- Acceso exitoso a alumnos online activos en ventana de apertura.
- Redirección y bloqueo a alumnos online expirados (`today > due_date`).
- Acceso exitoso a alumnos con admisiones mixtas (lote tradicional expirado + online activo).
- Funcionamiento intacto para admisiones tradicionales por lote.

## Documentación
- Creado el archivo de especificación y uso en `doc/modules/extrairg/irg_online_subject_portal_visibility.md`.
