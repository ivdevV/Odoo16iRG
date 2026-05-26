# Referencia Técnica: irg_campus_certificates_portal (V2.1)

Este documento provee la especificación técnica completa y de referencia para el módulo `irg_campus_certificates_portal`, actualizado para la versión V2.1.

---

## Ficha Técnica

| Propiedad | Valor |
| --- | --- |
| **Nombre Técnico** | `irg_campus_certificates_portal` |
| **Categoría** | Website |
| **Versión** | `16.0.2.1.0` (V2.1) |
| **Licencia** | LGPL-3 |
| **Instalable** | Sí |
| **Aplicación** | No |
| **Autor** | iRG |

### Dependencias

El módulo interactúa y depende de los siguientes componentes del sistema:
- `website` (Módulo nativo de Odoo para el Sitio Web)
- `portal` (Estructura base del portal del cliente)
- `irg_generacion_diplomas` (Gestión académica de diplomas del estudiante)
- `irg_gradebook_certificates` (Solicitud y generación de certificados de notas)
- `irg_tfm_acta_documento` (Gestión de actas académicas de TFM/TFG)
- `isep_website_custom` (Personalización visual y del portal de ISEP)
- `irg_course_portal_tiles` (Gestión de los mosaicos/tarjetas del dashboard)

---

## Descripción General

El módulo `irg_campus_certificates_portal` centraliza el acceso, la visualización y la descarga de documentos académicos desde el portal del alumno. Reúne en una sola interfaz con pestañas (`/campus/certificates`):
1. **Mis Diplomas:** Expedientes y certificados oficiales de titulación (`irg.diploma.registry`).
2. **Actas TFM/TFG:** Calificaciones de actas finales de defensa de trabajos de fin de grado y máster (`irg.tfm.acta`).
3. **Solicitudes de Notas / Certificados:** Peticiones y boletines de notas del estudiante (`irg.certificate.request`).

### Cambios Clave en V2.1
- **Reubicación del Tile de Acceso:** En lugar de mostrarse de forma global en el dashboard principal de `/campus`, el Tile "Certificados y Diplomas" se integra directamente dentro de la sección **"Herramientas del curso"** en la ficha individual de cada programa académico.
- **Soporte Multidocumento Ampliado:** Se añaden nuevas opciones de solicitud de certificados:
  - **Certificado de Notas Parcial** (`gradebook_partial`)
  - **Certificado de Asistencia** (`attendance`)
  - **Certificado de Matrícula** (`enrollment`)
- **Flexibilidad de Libretas en Progreso:** Los nuevos tipos de documento (`gradebook_partial`, `attendance`, `enrollment`) pueden ser solicitados aunque la libreta académica del estudiante esté en progreso (`in_progress`), a diferencia del Certificado de Notas Completo (`gradebook`) y del Diploma (`diploma`), que exigen obligatoriamente que la libreta esté finalizada y cerrada (`done`).

---

## Diseño Técnico

### Controladores Heredados e Interfaz
El controlador principal se hereda de la clase `CertificatePortalController` del módulo `irg_gradebook_certificates`.

```python
class IrgCampusCertificatesPortal(CertificatePortalController):
```

#### Rutas y Endpoints
El controlador gestiona los siguientes endpoints HTTP principales para usuarios autenticados:

1. **`/campus/certificates` (GET, auth='user')**
   * **Descripción:** Carga el listado unificado (diplomas, actas de TFM/TFG y solicitudes).
   * **Filtros:** Muestra registros vinculados a la ficha de estudiante (`op.student`) correspondiente al `res.partner` de la sesión activa.

2. **`/campus/certificates/new` (GET y POST, auth='user')**
   * **GET:** Carga el formulario de nueva solicitud.
     * **Preselección por Curso:** Permite recibir un parámetro opcional `course_id` en la query URL (ej: `/campus/certificates/new?course_id=3`). Si se provee, el dropdown de selección de programa/libreta (`gradebook_select`) preselecciona automáticamente el registro correspondiente para mejorar la experiencia del usuario.
   * **POST:** Procesa la creación de la solicitud (`irg.certificate.request`).
     * **Validaciones de Estado de Libreta:**
       * Si se solicita un **Certificado de Notas Completo** (`gradebook`) o un **Diploma** (`diploma`), la libreta seleccionada debe estar en estado cerrado (`state == 'done'`). De lo contrario, se deniega la petición con un mensaje de alerta.
       * Si se solicita un **Certificado de Notas Parcial** (`gradebook_partial`), **Certificado de Asistencia** (`attendance`), o **Certificado de Matrícula** (`enrollment`), se permite la creación con libretas activas en progreso (`state == 'in_process'` u otros no draft/cancelled).
       * No se admiten libretas en estado borrador (`draft`) o cancelado (`cancelled`).
     * **Control de Impagos:** Si el estudiante tiene cuotas de matrícula vencidas o pendientes de cobro (evaluado dinámicamente mediante `student.get_subscription_data()`), se bloquea la solicitud y se le indica que debe regularizar su situación.

3. **`/campus/certificates/download/diploma/<int:diploma_id>` (GET, auth='user')**
   * **Descripción:** Descarga segura del diploma oficial en formato PDF.

4. **`/campus/certificates/download/acta/<int:acta_id>` (GET, auth='user')**
   * **Descripción:** Descarga segura del acta de TFM/TFG en formato PDF.

### Vistas y Herencia QWeb (UI)

El módulo personaliza la experiencia del portal mediante herencia en las siguientes vistas:

1. **Mosaico en Ficha de Programa (`views/campus_dashboard_override.xml`)**
   * Hereda de `irg_course_portal_tiles.irg_user_profile_content_details_inherit` e inserta el Tile de "Certificados y Diplomas" dentro de las **Herramientas del curso** de un programa específico.
   * Pasa dinámicamente el `course_id` del programa en el enlace:
     ```html
     t-attf-href="/campus/certificates?course_id=#{op_course_id}"
     ```

2. **Diseño del Portal de Certificados (`views/portal_templates.xml`)**
   * **Listado de Certificados (`portal_certificate_list_override`):** Reemplaza el contenedor de `irg_gradebook_certificates.portal_certificate_list`. Implementa navegación por pestañas de Bootstrap 5 ("Mis Diplomas", "Actas TFM/TFG", "Solicitudes de Certificados") y tablas interactivas con estados de solicitudes (ej. pagos con Stripe/Redsys, número de tracking de envío postal).
   * **Formulario de Nueva Solicitud (`portal_certificate_new_override`):** Reemplaza el contenedor de `irg_gradebook_certificates.portal_certificate_new`. Adapta el formulario para soportar la selección del nuevo set de documentos y añade código JavaScript dinámico que:
     - Muestra campos condicionales (ej. transportista/mensajería si es certificado físico, u opciones especiales y texto libre si es personalizado).
     - Calcula en tiempo real el desglose de precios (precio base + gastos de envío).
     - Muestra un mensaje de advertencia visual y deshabilita el botón de envío si se selecciona Notas Completo o Diploma en un programa en curso.

---

## Seguridad y Control de Accesos

### Auditoría del Security Advisor (Veredicto: YES)

> [!IMPORTANT]
> Los estudiantes del portal pertenecen al grupo base `base.group_portal`, el cual carece de permisos de lectura nativos en base de datos (`ir.model.access.csv`) para las tablas académicas `irg.diploma.registry` y `irg.tfm.acta`.

Para resolver esto sin comprometer la seguridad ni provocar fallos 403 Forbidden, el módulo aplica las siguientes medidas validadas:

1. **Elevación de Privilegios Controlada (`.sudo()`):**
   * Los controladores consultan la base de datos con `.sudo()` únicamente para recuperar el registro y leer el archivo PDF binario adjunto (`ir.attachment`).

2. **Validación Estricta de Propietario (Ownership Validation):**
   * Para evitar vulnerabilidades de enumeración horizontal (ID IDOR, donde un alumno cambia el número en la URL de descarga para acceder a documentos ajenos), el controlador verifica rigurosamente que el `res.partner` de la sesión del usuario coincida con el `partner_id` del estudiante asociado al documento:
     ```python
     if not diploma.exists() or diploma.student_id.partner_id.id != partner.id or diploma.state != 'valid':
         return request.redirect('/campus/certificates')
     ```
   * En caso de discrepancia, se realiza una redirección silenciosa y segura al portal del alumno sin revelar la existencia del archivo.

3. **Bloqueo por Deudas de Matrícula:**
   * Se comprueba si el estudiante tiene pagos atrasados antes de procesar el formulario de solicitud:
     ```python
     if student and hasattr(student, 'get_subscription_data'):
         sub_data = student.get_subscription_data()
         if sub_data.get('t_adeuda') or (sub_data.get('t_amount_due_data') or 0) > 0:
             return _render_error(_('No puedes solicitar un certificado mientras tengas cuotas de matrícula pendientes...'))
     ```

---

## Suite de Pruebas Automatizadas

El módulo cuenta con pruebas de integración y simulación HTTP en `tests/test_portal.py` (etiquetadas como `post_install` y `-at_install`), las cuales cubren los flujos críticos del portal:

* **`test_01_campus_certificates_unauthorized_redirects`**
  * **Propósito:** Validar que los usuarios anónimos o invitados no autorizados sean redirigidos a la pantalla de login al intentar entrar al listado.
* **`test_02_campus_certificates_authorized_success`**
  * **Propósito:** Confirmar que un alumno autenticado en el portal puede ver el panel unificado y localizar sus diplomas y actas sin errores.
* **`test_03_download_diploma_and_acta`**
  * **Propósito:** Verificar que el flujo binario del archivo adjunto (PDF) se descarga correctamente cuando el alumno propietario lo solicita.
* **`test_04_download_other_student_document_fails`**
  * **Propósito:** Validar la protección contra vulnerabilidades IDOR. Si un estudiante intenta descargar un diploma o acta de otro alumno, el sistema lo bloquea y lo redirige de vuelta.
* **`test_05_portal_new_certificate_get_preselection`**
  * **Propósito:** Validar la preselección automática del programa en el formulario de solicitud cuando se pasa el parámetro `course_id` en la query.
* **`test_06_portal_new_certificate_post_validation`**
  * **Propósito:** Comprobar las restricciones de estado de libreta académica:
    - Falla si se solicita `gradebook` (Completo) o `diploma` con libreta en progreso.
    - Éxito si se solicita `gradebook_partial`, `attendance` o `enrollment` con libreta en progreso.
    - Éxito si se solicita `gradebook` o `diploma` con libreta finalizada (`done`).

---

## Guía de Instalación y Actualización

### En Entorno de Desarrollo Local

El contenedor de desarrollo Odoo local se ejecuta bajo el nombre de servicio `odoo16irg_local`.

```bash
# 1. Instalar el módulo por primera vez
docker exec -it odoo16irg_local odoo -c /etc/odoo/odoo.conf -d <nombre_bd> -i irg_campus_certificates_portal --stop-after-init

# 2. Actualizar el módulo para aplicar cambios en vistas o código
docker exec -it odoo16irg_local odoo -c /etc/odoo/odoo.conf -d <nombre_bd> -u irg_campus_certificates_portal --stop-after-init

# 3. Ejecutar los tests unitarios y de integración automatizados
docker exec -it odoo16irg_local odoo -c /etc/odoo/odoo.conf -d <nombre_bd> -i irg_campus_certificates_portal --test-enable --stop-after-init
```

### En Entorno de Producción

En producción, el contenedor principal de Odoo se identifica como `odoo_latest`.

```bash
# 1. Instalar el módulo en la base de datos de producción
docker exec -it odoo_latest odoo -c /etc/odoo/odoo.conf -d <nombre_bd> -i irg_campus_certificates_portal --stop-after-init

# 2. Actualizar el módulo tras realizar un pull de la rama de producción
docker exec -it odoo_latest odoo -c /etc/odoo/odoo.conf -d <nombre_bd> -u irg_campus_certificates_portal --stop-after-init
```
