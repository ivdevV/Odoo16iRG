# Changelog - 16 de Junio de 2026

## Proyecto: Descarga de Diplomados en el Portal del Alumno (`portal-download-diplomados`)

Este registro de cambios detalla las modificaciones e implementaciones realizadas para habilitar la visualización y descarga segura de diplomados y posgrados desde el portal web del campus del estudiante en Odoo 16.

---

### [16.0.1.0.0] - 2026-06-16

### Añadido
- **Nuevo módulo `irg_campus_diplomados_portal`**: Creado para encapsular la integración del portal del alumno con la descarga de diplomados de manera aislada e independiente.
- **Controlador del Portal (`controllers/portal.py`)**:
  - Clase `IrgCampusDiplomadosPortal` que extiende el controlador base `/campus/certificates` usando herencia limpia.
  - Endpoint de descarga segura en `/campus/certificates/download/diplomado/<int:diplomado_id>`.
- **Vista de Portal QWeb (`views/portal_templates.xml`)**:
  - Alerta de error en la cabecera si el usuario intenta descargar un diplomado bloqueado por rendimiento académico (`error=grade_too_low`).
  - Subsección "Diplomas de Posgrados y Diplomados" dentro de la pestaña de certificados (`#diplomas-pane`).
  - Lógica de renderizado dinámico: botón de descarga activo si se aprueba, o badge de "Bloqueado" con icono de candado si la nota es insuficiente.
- **Seguridad Backend y Protección de Descarga**:
  - Control de propiedad del diploma (valida que el registro pertenezca al `partner_id` del usuario autenticado).
  - Criterio de restricción académica: valida que la calificación final en la libreta del alumno (`app.gradebook.student`) sea **estrictamente mayor a 7.0**.
  - Mecanismo de generación en caliente: invoca `.action_reprint()` si el registro es válido pero el binario adjunto no existe o está vacío.
- **Tests de Integración HTTP (`tests/test_portal.py`)**:
  - Suite de pruebas completa que valida: el renderizado correcto del portal, la visualización de registros activos y bloqueados, la descarga exitosa de PDFs autorizados y la redirección con error si se intenta forzar la descarga de un diploma con nota baja.

### Documentación
- Creación de la especificación técnica en `.agents/knowledge/odoo_development_modding/artifacts/portal_diplomados_download.md`.
- Creación de la especificación y manual de usuario del módulo en `doc/modules/extrairg/irg_campus_diplomados_portal.md`.
- Actualización de la documentación del módulo base en `doc/modules/extrairg/irg_generacion_diplomados.md` para reflejar con precisión los campos de texto plano y el diseño a hoja completa (Full Bleed).
