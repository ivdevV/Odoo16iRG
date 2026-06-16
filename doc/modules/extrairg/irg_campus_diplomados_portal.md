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

La descarga de los diplomados y posgrados está sujeta a una **validación estricta de rendimiento académico**: el estudiante debe contar con una calificación final superior a **7.0** en su libreta de calificaciones (`app.gradebook.student`) para el curso del diplomado correspondiente. Si no alcanza esta nota, el sistema bloquea visualmente el botón en el portal y rechaza cualquier solicitud directa de descarga por URL.

---

## Funcionalidades principales

- **Listado Unificado:** Muestra los diplomados emitidos al estudiante dentro del portal de certificados, integrándose visualmente con el resto de diplomas de la plataforma.
- **Validación Académica:** Verifica en tiempo real la calificación final de la libreta académica del estudiante.
- **Acceso Restringido y Seguro:** Oculta los enlaces de descarga directa y muestra una insignia de **"Bloqueado"** con candado si el alumno no supera la nota final de 7.0. Además, protege el endpoint del controlador para validar de nuevo la nota y el partner propietario del diploma antes de servir el PDF.
- **Regeneración en Caliente:** Si un alumno cumple las condiciones pero su registro histórico no tiene un archivo adjunto PDF almacenado, el sistema intenta ejecutar la reimpresión automática (`action_reprint()`) para servir el archivo al vuelo.

---

## Modelos Utilizados

El módulo no crea nuevos modelos persistentes, sino que actúa como una capa de servicio e integración sobre modelos de otros módulos:

| Modelo | Módulo de Origen | Uso / Descripción |
|--------|------------------|-------------------|
| `irg.diplomado.registry` | `irg_generacion_diplomados` | Registro histórico de diplomados emitidos. Se utiliza para listar y obtener el PDF adjunto (`attachment_id`). |
| `app.gradebook.student` | `irg_academic_request_history` (base) | Libreta de calificaciones del estudiante. Se consulta el campo `total_final` para verificar el rendimiento académico. |
| `op.student` | `openeducat_core` | Ficha del alumno. Sirve para relacionar el usuario logueado en el portal (`res.partner`) con sus inscripciones y diplomados. |

---

## Controladores y Endpoints

### 1. Extensión del listado de certificados (`/campus/certificates`)
- **Método:** `GET`
- **Autenticación:** `user` (Usuario autenticado en el portal)
- **Descripción:** Extiende el controlador original `IrgCampusCertificatesPortal` mediante herencia de clases. Recupera los registros de diplomados asociados al partner del usuario y, para cada uno, busca su libreta de notas para determinar la calificación final y el estado de descarga (`can_download`). Expone esta información en `qcontext['diplomados_data']`.

### 2. Endpoint de descarga directa (`/campus/certificates/download/diplomado/<int:diplomado_id>`)
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
- **Subsección de Posgrados y Diplomados:** Añadida como pestaña o sección inside de `#diplomas-pane`. Muestra una tabla estilizada con el folio, curso, calificación (con colores dinámicos: verde para aprobado, rojo para insuficiente), fecha y tipo.
- **Botones Dinámicos:**
  - Si `can_download` es verdadero: Renderiza un botón `<a class="btn btn-sm btn-outline-primary">` que apunta al endpoint de descarga.
  - Si `can_download` es falso: Muestra una etiqueta `<span class="badge bg-danger-subtle text-danger">` con un candado y el texto "Bloqueado".

---

## Pruebas de Integración Automatizadas

El módulo incluye tests de integración HTTP localizados en `tests/test_portal.py`:

- **Caso Evaluado (`test_01_diplomados_portal_list_and_download`):**
  - Autentica a un usuario portal de prueba.
  - Comprueba que la página del portal carga correctamente (HTTP 200).
  - Valida la presencia de un diplomado aprobado (ejemplo: nota `8.5`) y un diplomado bloqueado (ejemplo: nota `6.0`).
  - Intenta la descarga autorizada del PDF y comprueba que se descargue el archivo correcto.
  - Intenta la descarga forzada por URL del diplomado bloqueado, verificando que el controlador lo impida, redirigiendo a la pantalla principal con la alerta de error `error=grade_too_low`.

### Comando de Ejecución de Tests
```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_campus_diplomados_portal --test-enable --test-tags=irg_campus_diplomados_portal --stop-after-init --log-level=info
```
