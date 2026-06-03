# Referencia Técnica: irg_certificate_attendance

Este documento provee la especificación técnica completa y de referencia para el módulo `irg_certificate_attendance`.

---

## Ficha Técnica

| Propiedad | Valor |
| --- | --- |
| **Nombre Técnico** | `irg_certificate_attendance` |
| **Categoría** | Academic / Website |
| **Versión** | `16.0.1.0.0` |
| **Licencia** | LGPL-3 |
| **Instalable** | Sí |
| **Aplicación** | No |
| **Autor** | iRG |

### Dependencias

El módulo interactúa y depende de los siguientes componentes del sistema:
- `irg_gradebook_certificates` (Módulo base de gestión de solicitudes de certificados)
- `irg_campus_certificates_portal` (Interfaz unificada de certificados en el portal)
- `irg_op_course_modality` (Gestión de modalidades académicas de cursos en iRG)

---

## Descripción General

## Descripción General

El módulo `irg_certificate_attendance` permite a los alumnos solicitar y generar **Certificados de Asistencia** para sesiones específicas de clases en directo en programas de tipo **HomeClass** (definidos por tener la modalidad con código `homeclass` en el curso o por pertenecer a un grupo con código `HC`).

### Características principales:
- **Restricción de Modalidad (HomeClass):** La opción de solicitar un certificado de asistencia se limita rigurosamente a los programas académicos que tengan asignada la modalidad `homeclass` o lotes (batches) cuyo nombre o código contengan las siglas `HC`.
- **Selector de Sesiones en Portal:** En el formulario de nueva solicitud, al elegir el tipo de documento "Certificado de Asistencia", se inyecta dinámicamente un selector que carga (vía AJAX/Fetch JSON) las sesiones de clase en directo en las que el alumno estuvo presente o aquellas sesiones activas/confirmadas del lote.
- **Detalle de Asistencia en el Certificado:** La plantilla Word (docx) se carga y reemplaza dinámicamente los campos genéricos para certificar la asistencia a una clase en específico, indicando el título de la clase, la asignatura y la fecha de impartición formateada al español.

---

## Diseño Técnico

### 1. Modelos (`models/irg_certificate_request.py`)

Hereda el modelo base `irg.certificate.request` para añadir los campos y la lógica específica:

* **Campos añadidos:**
  - `session_id` (`Many2one` hacia `op.session`): Sesión de clase a la cual se certifica la asistencia.

* **Validaciones (`_validate_attendance_request`):**
  - Si el tipo de documento es `attendance`, la `session_id` es obligatoria.
  - Verifica de forma estricta que la libreta académica asociada cumpla al menos uno de los siguientes criterios de modalidad:
    - El curso asociado al estudiante tiene una modalidad (`irg_modality_ids`) con código `'homeclass'`.
    - El lote (`batch_id`) del estudiante tiene el código exactamente igual a `'HC'`, o contiene `'HC'` en su código o nombre (insensible a mayúsculas).
  - Si no se cumple ninguna de estas condiciones, se lanza un `ValidationError` impidiendo la creación o modificación de la solicitud.
  - Esta validación se ejecuta tanto en la creación (`create`) como en la edición (`write`).

* **Carga de Plantilla (`_get_template_path`):**
  - Si el tipo es `attendance`, busca y carga los archivos docx ubicados en `static/src/templates/` del propio módulo (`Plantilla-certificado-asistencia-dpto.docx` o `Plantilla-certificado-asistencia-raimon.docx` según el firmante).

* **Reemplazo Dinámico (`_fill_template`):**
  - Sobrescribe la lógica de llenado del documento Word.
  - Formatea la fecha de inicio de la sesión en español (ej. *"2 de junio de 2026"*).
  - Reemplaza el párrafo base de curso regular por:
    `a la clase "<<ClaseTema>>" de la asignatura "<<Asignatura>>" impartida el día <<fechaClase>>`

### 2. Controladores Web y API (`controllers/portal.py`)

Hereda de `IrgCampusCertificatesPortal` para controlar el flujo web y las peticiones AJAX:

* **Endpoint JSON `/campus/certificates/sessions` (POST, auth='user'):**
  - Recibe el parámetro `gradebook_id` y valida la propiedad del alumno para evitar vulnerabilidades de tipo IDOR (Insecure Direct Object Reference), asegurando que la libreta consultada pertenece al `partner` del usuario en sesión.
  - Obtiene el lote (`batch_id`) de la libreta.
  - Busca todas las sesiones de dicho lote (`op.session`).
  - Filtra las sesiones válidas aplicando las siguientes reglas:
    - Sesiones en las que el estudiante tiene un registro de asistencia (`op.attendance.line`) con `present = True`.
    - O bien, sesiones activas (`active = True`) y en estado confirmado (`confirm`) o finalizado (`done`).
  - Retorna un diccionario con una lista de diccionarios `sessions` que incluye los siguientes campos para poblar el dropdown del portal:
    - `id`: Identificador de la sesión.
    - `name`: Nombre técnico de la sesión.
    - `class_title`: Título de la clase (usa preferentemente el campo `class_title` si existe, cayendo en desuso al campo `name` como fallback).
    - `subject_name`: Nombre de la asignatura asociada.
    - `date`: Fecha de la sesión formateada como `YYYY-MM-DD`.

* **Formulario de Solicitud `/campus/certificates/new` (POST):**
  - Captura y procesa el parámetro `session_id`.
  - Ejecuta las mismas verificaciones de seguridad de backend para evitar solicitudes fraudulentas o manipulación de parámetros HTTP (IDOR y comprobación de modalidad HomeClass).
  - Redirecciona a la confirmación de pago del certificado si es exitoso.

### 3. Vistas y AJAX (`views/portal_templates.xml`)

* Hereda de `irg_campus_certificates_portal.portal_certificate_new_override` para añadir el campo de sesión.
* Implementa lógica JavaScript que escucha los eventos `change` en el selector de tipo de documento y el selector de libreta académica.
* Si el tipo es `attendance`, se invoca Fetch hacia `/campus/certificates/sessions` y se refrescan las opciones de sesiones al vuelo de forma asíncrona, mostrando u ocultando el bloque según corresponda.

---

## Suite de Pruebas Automatizadas

El módulo incluye un set de pruebas en `tests/test_attendance.py`:
- `test_01_attendance_requires_session`: Valida que sea imposible crear un registro tipo `attendance` sin asignarle una sesión (se lanza `ValidationError`).
- `test_02_attendance_restricted_to_homeclass_or_hc_batch`: Comprueba que no se permite crear una solicitud de asistencia en libretas normales de cursos presenciales u online que no pertenezcan a la modalidad HomeClass o lote HC (se lanza `ValidationError`).
- `test_03_attendance_allowed_on_hc_batch`: Verifica que se apruebe la creación de la solicitud si el lote (batch) del alumno tiene código "HC".
- `test_04_attendance_allowed_on_homeclass_modality`: Verifica que se apruebe la creación de la solicitud si el programa académico tiene asignada la modalidad HomeClass en el curso, incluso si el lote no es HC.
- `test_05_attendance_fill_template`: Comprueba la carga física de las plantillas Word de asistencia y el flujo completo de generación de PDF.

---

## Instalación y Pruebas Locales

```bash
# Instalar y ejecutar tests
docker exec -it odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -i irg_certificate_attendance --test-enable --stop-after-init
```

---

## Historial de Cambios (Changelog)

### [16.0.1.0.0] - 2026-06-03
- **Mejora:** Implementación de la lógica y flujos para Certificados de Asistencia.
- **Seguridad (IDOR):** Validación en el backend y en el controlador del portal para garantizar que la libreta y las sesiones correspondan al alumno autenticado.
- **Funcionalidad:**
  - Creación del endpoint `/campus/certificates/sessions` para la carga asíncrona de sesiones autorizadas.
  - Inserción dinámica del dropdown de selección de sesiones en el portal del alumno bajo el tipo de certificado de asistencia.
  - Filtro estricto de sesiones: requiere que el estudiante haya asistido (`present = True`) o que la sesión esté confirmada/terminada y activa.
- **Restricción de Acceso:** Limitación a programas académicos con modalidad `homeclass` o lotes con identificador `HC`.
- **Calidad:** Suite completa de tests unitarios verificando restricciones de modalidad, sesiones requeridas y renderizado correcto de la plantilla Word de asistencia.
