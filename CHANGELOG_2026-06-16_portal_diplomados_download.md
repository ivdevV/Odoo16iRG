# Changelog - 16 de Junio de 2026

## Proyecto: Descarga de Diplomados en el Portal del Alumno (`portal-download-diplomados`)

Este registro de cambios detalla las modificaciones e implementaciones realizadas para habilitar la visualización aislada, la solicitud gratuita y la descarga segura de diplomados y posgrados desde el portal web del campus del estudiante en Odoo 16.

---

### [16.0.1.0.0] - 2026-06-16

### Añadido
- **Nuevo módulo `irg_campus_diplomados_portal`**: Creado para encapsular la integración del portal del alumno con la descarga de diplomados de manera aislada e independiente.
- **Flujo de Trámite Gratuito de Diplomados**:
  - Modelo de Solicitudes (`irg.diplomado.request`) para registrar y realizar seguimiento de las solicitudes de expedición de diplomas gratuitas.
  - Endpoint `/campus/certificates/request/diplomado/<course_id>` para procesar la creación de nuevas solicitudes en estado `requested` previa validación académica.
- **Controlador del Portal (`controllers/portal.py`)**:
  - Clase `IrgCampusDiplomadosPortal` que extiende el controlador base `/campus/certificates` usando herencia limpia.
  - Endpoint de descarga segura en `/campus/certificates/download/diplomado/<int:diplomado_id>`.
  - Intercepción y filtrado en `/campus/certificates/new` (GET) para excluir los diplomados del desplegable del formulario de solicitudes generales de pago.
  - Intercepción y sanitización en `/campus/certificates/new` (POST) para invalidar envíos directos de red de solicitudes sobre diplomados, forzando la libreta a `'0'`.
  - Bandera `only_diplomados` que filtra el listado completo y oculta las demás secciones si se accede al portal con el parámetro GET `course_id` de un diplomado.
- **Vinculación Reactiva de Solicitudes**:
  - Sobrescritura del método `create` en `irg.diplomado.registry`. Al emitirse un diploma en el backend, busca solicitudes activas en el portal para ese estudiante/curso, asocia el ID del diploma generado y actualiza reactivamente el estado de la solicitud a `processed` (Procesado).
- **Vista de Portal QWeb (`views/portal_templates.xml`)**:
  - Pestaña independiente "Mis Diplomados" (`#diplomados-tab`) e icono `fa-certificate`.
  - Tres secciones diferenciadas dentro del panel `#diplomados-pane`:
    1. *Títulos Emitidos:* Descarga segura en PDF o insignia de candado.
    2. *Títulos Disponibles para Solicitar:* Botón amarillo "+ Solicitar Diploma" para tramitar la expedición directa y gratuita de títulos aprobados.
    3. *Expediciones en Trámite:* Visualización de solicitudes pendientes con un spinner animado.
  - Ocultamiento dinámico (mediante la bandera `only_diplomados`) de las pestañas base ("Mis Diplomas", "Actas TFM/TFG", "Solicitudes") y del botón superior "+ Nueva Solicitud".
  - Alerta de error en la cabecera si el usuario intenta descargar un diplomado bloqueado por rendimiento académico (`error=grade_too_low`).
- **Seguridad Backend y Protección de Descarga**:
  - Control de propiedad del diploma (valida que el registro pertenezca al `partner_id` del usuario autenticado).
  - Criterio de restricción académica: valida que la calificación final en la libreta del alumno (`app.gradebook.student`) sea **estrictamente mayor a 7.0**.
  - Mecanismo de generación en caliente: invoca `.action_reprint()` si el registro es válido pero el binario adjunto no existe o está vacío.
- **Tests de Integración HTTP (`tests/test_portal.py`)**:
  - Suite de pruebas de integración HTTP completa con **3 tests unitarios pasados con éxito**:
    1. `test_01_diplomados_portal_list_and_download`: Valida el correcto listado de diplomados aprobados y bloqueados, la descarga del PDF y sus redirecciones de error.
    2. `test_02_diplomados_request_form_exclusion`: Valida el filtrado del combobox en GET y el rechazo en POST para libretas de diplomados en solicitudes generales de pago.
    3. `test_03_diplomados_contextual_only_visibility_and_request`: Simula el acceso con `course_id` de diplomado ocultando pestañas base, el flujo de solicitud gratuita vía GET/POST, y la posterior transición de estado reactiva en la base de datos a `processed` al crearse el diploma en el backend.

### Documentación
- Actualización de la especificación técnica en `.agents/knowledge/odoo_development_modding/artifacts/portal_diplomados_download.md`.
- Actualización de la especificación y manual de usuario del módulo en `doc/modules/extrairg/irg_campus_diplomados_portal.md`.
- Actualización de la documentación del módulo base en `doc/modules/extrairg/irg_generacion_diplomados.md` para reflejar con precisión los campos de texto plano y el diseño a hoja completa (Full Bleed).
