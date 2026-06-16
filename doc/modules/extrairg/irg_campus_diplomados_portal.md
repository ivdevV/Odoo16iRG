# irg_campus_diplomados_portal

**Categoría:** extrairg  
**Versión:** 16.0.1.0.0  
**Licencia:** LGPL-3  
**Instalable:** Sí  
**Autor:** Instituto Raimon Gaja  
**Depende de:** `irg_campus_certificates_portal`, `irg_generacion_diplomados`  

---

## ¿Qué hace este módulo?

Este módulo integra los registros de diplomas generados a través de `irg_generacion_diplomados` en el portal del estudiante, permitiendo visualizar y descargar los documentos en formato PDF de manera segura y controlada desde el campus web de Odoo 16.

### Aislamiento e Independencia
Para evitar que los alumnos confundan los diplomados y posgrados (gratuitos e inmutables) con los certificados normales que conllevan tasas de pago de trámites, el módulo implementa:
1. **Aislamiento Visual:** Los diplomados se muestran en una pestaña independiente llamada "Mis Diplomados" en el portal de certificados, en lugar de estar mezclados en el listado base.
2. **Exclusión de Solicitudes:** Los diplomados y posgrados están completamente excluidos del formulario de solicitud de nuevos certificados (`/campus/certificates/new`), bloqueando la creación de solicitudes de pago asociadas a los mismos.

---

## Funcionalidades principales

- **Listado Unificado pero Aislado:** Muestra los diplomados emitidos al estudiante dentro del portal en su propia pestaña "Mis Diplomados".
- **Validación Académica:** Verifica en tiempo real la calificación final de la libreta académica del estudiante.
- **Acceso Restringido y Seguro:** Oculta los enlaces de descarga directa y muestra una insignia de **"Bloqueado"** con candado si el alumno no supera la nota final de 7.0. Además, protege el endpoint del controlador para validar de nuevo la nota y el partner propietario del diploma antes de servir el PDF.
- **Regeneración en Caliente:** Si un alumno cumple las condiciones pero su registro histórico no tiene un archivo adjunto PDF almacenado, el sistema intenta ejecutar la reimpresión automática (`action_reprint()`) para servir el archivo al vuelo.
- **Filtrado GET/POST en Solicitudes:** Elimina los diplomados del combobox de libretas en la solicitud de certificados (GET) e invalida a nivel de backend cualquier envío forzado por red para un diplomado (POST), forzando el ID de libreta académica a `'0'` para gatillar la validación de error nativa.

---

## Modelos Utilizados

El módulo no crea nuevos modelos persistentes, sino que actúa como una capa de servicio e integración sobre modelos de otros módulos:

| Modelo | Módulo de Origen | Uso / Descripción |
|--------|------------------|-------------------|
| `irg.diplomado.registry` | `irg_generacion_diplomados` | Registro histórico de diplomados emitidos. Se utiliza para listar y obtener el PDF adjunto (`attachment_id`). |
| `app.gradebook.student` | `irg_academic_request_history` (base) | Libreta de calificaciones del estudiante. Se consulta el campo `total_final` para verificar el rendimiento académico y el curso para saber si es diplomado. |
| `op.student` | `openeducat_core` | Ficha del alumno. Sirve para relacionar el usuario logueado en el portal (`res.partner`) con sus inscripciones y diplomados. |

---

## Controladores y Endpoints

### 1. Extensión del listado de certificados (`/campus/certificates`)
- **Método:** `GET`
- **Autenticación:** `user` (Usuario autenticado en el portal)
- **Descripción:** Extiende el controlador original `IrgCampusCertificatesPortal` mediante herencia de clases. Recupera los registros de diplomados asociados al partner del usuario y, para cada uno, busca su libreta de notas para determinar la calificación final y el estado de descarga (`can_download`). Expone esta información en `qcontext['diplomados_data']`.

### 2. Extensión del formulario de solicitudes (`/campus/certificates/new`)
- **Método:** `GET` y `POST`
- **Autenticación:** `user`
- **Descripción:** Controla el aislamiento y exclusión del flujo de pago de certificados:
  - **Filtro GET:** Al renderizar el formulario, filtra la lista de libretas académicas enviadas a la vista, excluyendo los cursos donde `is_diplomado()` sea verdadero.
  - **Filtro POST:** Al procesar el envío, si el usuario inyecta por red el ID de una libreta de diplomado, el controlador lo intercepta antes del comportamiento base y sobrescribe el parámetro `gradebook_id` con `'0'`. Esto fuerza al controlador nativo a devolver un error de formulario ("Selecciona la libreta"), bloqueando la creación del trámite.

### 3. Endpoint de descarga directa (`/campus/certificates/download/diplomado/<int:diplomado_id>`)
- **Método:** `GET`
- **Autenticación:** `user`
- **Parámetros:** `diplomado_id` (ID del registro histórico de diplomado)
- **Flujo de Seguridad:**
  1. Verifica que el registro de diplomado exista.
  2. Verifica que el diplomado pertenezca al partner del usuario autenticado (evita escalación de privilegios / ID Harvesting).
  3. Verifica que la nota final de la libreta académica asociada a ese alumno y curso sea estrictamente superior a **7.0**.
  4. Si alguna validación falla, redirige al portal. Si es por notas, redirige con el query param `error=grade_too_low`.
  5. Si las validaciones son correctas, descarga el adjunto PDF en el navegador.

---

## Vistas y UI (QWeb)

La plantilla se extiende en `views/portal_templates.xml` heredando de `irg_campus_certificates_portal.portal_certificate_list_override`:

- **Bloque de Mensaje de Error:** Se inyecta una alerta bootstrap de tipo peligro (`alert-danger`) si se detecta el parámetro `error=grade_too_low` en la URL.
- **Pestaña Independiente "Mis Diplomados":** Inyecta un botón `button` con ID `diplomados-tab` después de la pestaña base.
- **Contenedor Independiente "Mis Diplomados":** Inyecta una sección `div` con ID `diplomados-pane` y comportamiento fade de Bootstrap. Muestra la tabla estilizada con el folio, curso, calificación (con colores dinámicos: verde para aprobado, rojo para insuficiente), fecha, tipo, y el botón dinámico de descarga directa o insignia de candado.

---

## Pruebas de Integración Automatizadas

El módulo incluye tests de integración HTTP localizados en `tests/test_portal.py`:

- **`test_01_diplomados_portal_list_and_download`:**
  - Autentica a un usuario portal de prueba.
  - Comprueba que la página del portal carga correctamente (HTTP 200).
  - Valida la presencia de la pestaña independiente "Mis Diplomados" y de los diplomados correspondientes.
  - Valida el funcionamiento del botón de descarga para el alumno aprobado (nota `8.5`) y la insignia de "Bloqueado" para el reprobado (nota `6.0`), así como el bloqueo de URL directa con redirección por calificación baja.
- **`test_02_diplomados_request_form_exclusion`:**
  - Valida que al cargar el formulario de nueva solicitud, los cursos de tipo diplomado estén excluidos de la lista desplegable, pero los cursos normales de máster se muestren correctamente.
  - Simula una petición maliciosa tipo POST enviando directamente el ID de la libreta del diplomado, comprobando que el backend lo intercepte, lo limpie a `'0'` y el formulario lo rechace con el error nativo "Selecciona la libreta".

### Comando de Ejecución de Tests
```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_campus_diplomados_portal --test-enable --test-tags=irg_campus_diplomados_portal --stop-after-init --log-level=info
```
