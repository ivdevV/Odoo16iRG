# Changelog - 16 de Junio de 2026

## Proyecto: Descarga de Diplomados en el Portal del Alumno (`portal-download-diplomados`)

Este registro de cambios detalla las modificaciones e implementaciones realizadas para habilitar la visualización aislada y la descarga segura de diplomados y posgrados desde el portal web del campus del estudiante en Odoo 16.

---

### [16.0.1.0.0] - 2026-06-16

### Añadido
- **Nuevo módulo `irg_campus_diplomados_portal`**: Creado para encapsular la integración del portal del alumno con la descarga de diplomados de manera aislada e independiente.
- **Controlador del Portal (`controllers/portal.py`)**:
  - Clase `IrgCampusDiplomadosPortal` que extiende el controlador base `/campus/certificates` usando herencia limpia.
  - Endpoint de descarga segura en `/campus/certificates/download/diplomado/<int:diplomado_id>`.
  - Intercepción y filtrado en `/campus/certificates/new` (GET) para excluir los diplomados del desplegable del formulario de solicitud.
  - Intercepción y sanitización en `/campus/certificates/new` (POST) para invalidar envíos directos de red de solicitudes sobre diplomados, forzando la libreta a `'0'`.
- **Vista de Portal QWeb (`views/portal_templates.xml`)**:
  - Pestaña independiente "Mis Diplomados" (`#diplomados-tab`) e icono `fa-certificate`.
  - Contenedor independiente de pestaña (`#diplomados-pane`) que aísla visualmente los títulos de posgrado y diplomado de los diplomas regulares de pago.
  - Alerta de error en la cabecera si el usuario intenta descargar un diplomado bloqueado por rendimiento académico (`error=grade_too_low`).
  - Lógica de renderizado dinámico: botón de descarga activo si se aprueba, o badge de "Bloqueado" con icono de candado si la nota es insuficiente.
- **Seguridad Backend y Protección de Descarga**:
  - Control de propiedad del diploma (valida que el registro pertenezca al `partner_id` del usuario autenticado).
  - Criterio de restricción académica: valida que la calificación final en la libreta del alumno (`app.gradebook.student`) sea **estrictamente mayor a 7.0**.
  - Mecanismo de generación en caliente: invoca `.action_reprint()` si el registro es válido pero el binario adjunto no existe o está vacío.
- **Tests de Integración HTTP (`tests/test_portal.py`)**:
  - Suite de pruebas completa con **2 tests unitarios pasados con éxito**:
    1. `test_01_diplomados_portal_list_and_download`: Valida el listado en la pestaña independiente, los estados de descarga/bloqueo y el endpoint seguro de descarga del PDF.
    2. `test_02_diplomados_request_form_exclusion`: Valida el filtrado del combobox en GET y el rechazo con error del formulario en peticiones POST para libretas de diplomados.

### Documentación
- Actualización de la especificación técnica en `.agents/knowledge/odoo_development_modding/artifacts/portal_diplomados_download.md`.
- Actualización de la especificación y manual de usuario del módulo en `doc/modules/extrairg/irg_campus_diplomados_portal.md`.
- Actualización de la documentación del módulo base en `doc/modules/extrairg/irg_generacion_diplomados.md` para reflejar con precisión los campos de texto plano y el diseño a hoja completa (Full Bleed).
