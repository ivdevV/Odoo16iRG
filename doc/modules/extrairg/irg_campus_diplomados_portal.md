# irg_campus_diplomados_portal

**Categoría:** extrairg  
**Versión:** 16.0.1.0.0  
**Licencia:** LGPL-3  
**Instalable:** Sí  
**Autor:** Instituto Raimon Gaja  
**Depende de:** `irg_campus_certificates_portal`, `irg_generacion_diplomados`  

---

## ¿Qué hace este módulo?

Este módulo integra los registros de diplomas generados a través de `irg_generacion_diplomados` en el portal del estudiante, permitiendo visualizar, solicitar de forma gratuita y descargar los documentos en formato PDF de manera segura y controlada desde el campus web de Odoo 16.

### Aislamiento e Independencia
Para evitar que los alumnos confundan los diplomados y posgrados (gratuitos e inmutables) con los certificados normales que conllevan tasas de pago de trámites, el módulo implementa:
1. **Aislamiento Visual:** Los diplomados se muestran en una pestaña independiente llamada "Mis Diplomados" en el portal de certificados.
2. **Exclusión de Solicitudes de Pago:** Los diplomados y posgrados están completamente excluidos del formulario de solicitud de nuevos certificados base (`/campus/certificates/new`), bloqueando la creación de solicitudes de pago asociadas a los mismos.
3. **Flujo de Solicitud Directo y Gratuito:** El alumno puede tramitar su solicitud directamente desde la pestaña "Mis Diplomados" sin coste alguno.

---

## Funcionalidades principales

- **Pestaña Independiente "Mis Diplomados":** Organizada en tres subsecciones para guiar al estudiante de forma clara:
  1. **Títulos Emitidos:** Listado de diplomados con calificación y el botón de descarga del PDF (o insignia de "Bloqueado" si la nota es insuficiente).
  2. **Títulos Disponibles para Solicitar:** Muestra los cursos finalizados con nota final superior a 7.0 que aún no tienen un diploma emitido ni una solicitud activa. Contiene un botón para realizar el trámite de expedición gratuita de manera inmediata.
  3. **Expediciones en Trámite:** Muestra las solicitudes enviadas por el portal en estado "En trámite" que están pendientes de proceso en el backend.
- **Validación Académica:** Verifica en tiempo real la calificación final de la libreta académica del estudiante (nota final `> 7.0`).
- **Acceso Restringido y Seguro:** Oculta los enlaces de descarga directa y muestra una insignia de **"Bloqueado"** con candado si el alumno no supera la nota final de 7.0. Además, protege el endpoint del controlador para validar de nuevo la nota y el partner propietario del diploma antes de servir el PDF.
- **Regeneración en Caliente:** Si un alumno cumple las condiciones pero su registro histórico no tiene un archivo adjunto PDF almacenado, el sistema intenta ejecutar la reimpresión automática (`action_reprint()`) para servir el archivo al vuelo.
- **Filtrado GET/POST en Solicitudes Base:** Elimina los diplomados del combobox de libretas en la solicitud de certificados general (GET) e invalida a nivel de backend cualquier envío forzado por red para un diplomado (POST), forzando el ID de libreta académica a `'0'` para gatillar la validación de error nativa.
- **Visibilidad Contextual Dinámica:** Si se accede al portal de certificados con un parámetro de URL `course_id` de tipo diplomado, el sistema oculta dinámicamente el botón de nueva solicitud y las demás pestañas para enfocar al alumno en la gestión de su diplomado.
- **Transición y Vinculación Reactiva:** Cuando administración genera el registro del diplomado (`irg.diplomado.registry`), el modelo intercepta el `create` y asocia el nuevo diploma a la solicitud pendiente (`irg.diplomado.request`), cambiando su estado a "Procesado" de forma automática.

---

## Modelos Utilizados

El módulo utiliza modelos específicos de integración y extiende los modelos existentes:

| Modelo | Tipo | Uso / Descripción |
|--------|------|-------------------|
| `irg.diplomado.request` | Nuevo | Almacena y trackea las solicitudes de expedición de diplomas gratuitas, con estados `requested` (Solicitado), `processed` (Procesado) y `cancelled` (Cancelado). |
| `irg.diplomado.registry` | Extensión | Sobrescribe el método `create` para asociar reactivamente el diploma y actualizar el estado de las solicitudes a `processed`. |
| `app.gradebook.student` | Extensión (base) | Libreta de calificaciones del estudiante. Se consulta el campo `total_final` para verificar el rendimiento académico y el curso para saber si es diplomado. |
| `op.student` | Extensión (base) | Ficha del alumno. Sirve para relacionar el usuario logueado en el portal (`res.partner`) con sus inscripciones, solicitudes y diplomados. |

---

## Controladores y Endpoints

### 1. Extensión del listado de certificados (`/campus/certificates`)
- **Método:** `GET`
- **Autenticación:** `user`
- **Descripción:** Extiende el controlador base. Recupera la lista de diplomados, las solicitudes pendientes y los cursos aptos para solicitar. Aplica filtrado de contexto por `course_id` si el parámetro GET está presente y corresponde a un diplomado, forzando la bandera `only_diplomados = True`.

### 2. Extensión del formulario de solicitudes de pago (`/campus/certificates/new`)
- **Método:** `GET` y `POST`
- **Autenticación:** `user`
- **Descripción:** Excluye el combo de libretas del formulario de la selección de diplomados (GET) e invalida el envío directo POST forzando la libreta a `'0'` si se inyecta un diplomado.

### 3. Trámite de nueva solicitud de diplomado (`/campus/certificates/request/diplomado/<int:course_id>`)
- **Método:** `GET` y `POST`
- **Autenticación:** `user`
- **Descripción:** Crea un registro en `irg.diplomado.request` en estado `requested`. Valida previamente que la libreta académica del estudiante en ese curso esté finalizada y tenga nota `> 7.0`, y que no existan solicitudes ni diplomas previos activos. Redirige al listado con `request_success=1`.

### 4. Endpoint de descarga directa (`/campus/certificates/download/diplomado/<int:diplomado_id>`)
- **Método:** `GET`
- **Autenticación:** `user`
- **Descripción:** Valida la propiedad del diploma y nota `> 7.0` en la libreta. Si es correcto, sirve el PDF adjunto (y lo genera en caliente si está ausente).

---

## Vistas y UI (QWeb)

La plantilla se extiende en `views/portal_templates.xml` heredando de `irg_campus_certificates_portal.portal_certificate_list_override`:

- **Bloque de Mensaje de Error:** Se inyecta una alerta bootstrap de tipo peligro (`alert-danger`) si se detecta el parámetro `error=grade_too_low` en la URL.
- **Pestaña y Panel Independiente "Mis Diplomados":** Inyecta un botón y un contenedor fade de Bootstrap con las tres subsecciones de Títulos Emitidos, Disponibles para Solicitar y Expediciones en Trámite.
- **Ocultamiento Dinámico:** Si `only_diplomados` es verdadero, se ocultan mediante condicionales las pestañas base ("Mis Diplomas", "Actas TFM/TFG", "Solicitudes") y el botón superior "+ Nueva Solicitud".

---

## Pruebas de Integración Automatizadas

El módulo incluye tests de integración HTTP localizados en `tests/test_portal.py`:

- **`test_01_diplomados_portal_list_and_download`:** Valida listado, estados de descarga y descarga directa/bloqueos de PDF.
- **`test_02_diplomados_request_form_exclusion`:** Valida que el formulario general de solicitudes de pago no permita listar ni tramitar diplomados.
- **`test_03_diplomados_contextual_only_visibility_and_request`:** Valida el acceso contextual por URL ocultando las pestañas base, el envío del flujo de solicitud gratuita, y la posterior transición automática y vinculación reactiva del estado de la solicitud a `processed` cuando el diploma es creado en el backend.

### Comando de Ejecución de Tests
```bash
docker exec odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -u irg_campus_diplomados_portal --test-enable --test-tags=irg_campus_diplomados_portal --stop-after-init --log-level=info
```
