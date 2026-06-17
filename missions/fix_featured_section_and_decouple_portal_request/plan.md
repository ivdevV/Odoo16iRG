# Misión: Corrección de error en Destacados, desacoplamiento y reubicación de Tiles de Certificados/Diplomas

## Alcance y Objetivos
1. Corregir el `AccessError: No puede ingresar a los registros 'Tema' (op.subject)` que sufren los estudiantes al acceder a la sección de contenidos destacados.
2. Desacoplar el módulo `irg_diplomado_portal_request` del módulo `irg_campus_certificates_portal` eliminando la dependencia física en el manifest y heredando de la plantilla de base de tiles.
3. Corregir la ubicación de los tiles "Certificados y Diplomas" y "Diploma del Diplomado" en el portal para que aparezcan en la sección "Herramientas del curso" (en lugar de inyectarse incorrectamente en la fila de asignaturas curriculares).

## Clasificación de Complejidad
- **Clasificación:** `standard`
- **Justificación:** Afecta a 5 archivos en 3 módulos custom (`irg_course_elearning_featured_section`, `irg_diplomado_portal_request`, y `irg_campus_certificates_portal`). No introduce cambios de base de datos ni afecta autenticación o datos críticos.

## Modelos Elegidos para cada Fase
- **Plan:** Orquestador (Gemini 3.5 Flash)
- **Implementación:** Codificador (Gemini 3.5 Flash)
- **Validación:** Testeador (Gemini 3.5 Flash)
- **Documentación:** Documentador (Gemini 3.5 Flash)

## Tareas Propuestas
1. Modificar `slide_channel.py` en `irg_course_elearning_featured_section` para acceder de forma segura a `op_subject_ids` utilizando `sudo()`.
2. Remover la dependencia `irg_campus_certificates_portal` en `__manifest__.py` de `irg_diplomado_portal_request`.
3. Ajustar la herencia en `course_portal_tiles.xml` de `irg_diplomado_portal_request` para heredar directamente de `irg_course_portal_tiles.irg_user_profile_content_details_inherit` y usar un XPath más robusto apuntando a "Herramientas del curso".
4. Corregir los tests de `irg_diplomado_portal_request/tests/test_portal.py` reflejando el desacoplamiento del tile.
5. Ajustar la herencia y el XPath en `campus_dashboard_override.xml` de `irg_campus_certificates_portal` para apuntar a la fila correcta de "Herramientas del curso" y evitar que se inyecte en la sección de asignaturas. Añadir control dinámico con `t-if="not hasattr(course_id, 'irg_is_diplomado') or not course_id.irg_is_diplomado()"`.
