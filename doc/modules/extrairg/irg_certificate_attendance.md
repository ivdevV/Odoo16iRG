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

El módulo `irg_certificate_attendance` permite a los alumnos solicitar y generar "Certificados de Asistencia" para sesiones específicas de clases en directo en programas de tipo **HomeClass** (definidos por tener la modalidad con código `homeclass` en el curso o por pertenecer a un grupo con código `HC`).

### Características principales:
- **Restricción por Modalidad:** La opción de solicitar un certificado de asistencia se limita rigurosamente a los programas académicos de la modalidad HomeClass o grupos que contengan `HC`.
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
  - Verifica que la libreta académica asociada pertenezca a un curso con modalidad `homeclass` o que el lote del estudiante tenga código o nombre que contenga `HC`.
  - Esta validación se ejecuta de forma estricta tanto en la creación (`create`) como en la edición (`write`).

* **Carga de Plantilla (`_get_template_path`):**
  - Si el tipo es `attendance`, busca y carga los archivos docx ubicados en `static/src/templates/` del propio módulo (`Plantilla-certificado-asistencia-dpto.docx` o `Plantilla-certificado-asistencia-raimon.docx` según el firmante).

* **Reemplazo Dinámico (`_fill_template`):**
  - Sobrescribe la lógica de llenado del documento Word.
  - Formatea la fecha de inicio de la sesión en español (ej. *"2 de junio de 2026"*).
  - Reemplaza el párrafo base de curso regular por:
    `a la clase "<<ClaseTema>>" de la asignatura "<<Asignatura>>" impartida el día <<fechaClase>>`

### 2. Controladores Web (`controllers/portal.py`)

Hereda de `IrgCampusCertificatesPortal` para controlar el flujo web y las peticiones AJAX:

* **Endpoint JSON `/campus/certificates/sessions` (POST, auth='user'):**
  - Recibe el `gradebook_id` y valida la propiedad del alumno (para evitar vulnerabilidades IDOR).
  - Filtra las sesiones del lote (`op.session`). Muestra únicamente las sesiones en las que el alumno figura como presente (`present = True` en `op.attendance.line`) o aquellas que se encuentren activas y en estado `confirm` o `done`.
  - Retorna un arreglo JSON con el ID, nombre, título, asignatura y fecha de las clases.

* **Sobrescritura del formulario de solicitud `/campus/certificates/new` (POST):**
  - Captura el campo `session_id`.
  - Realiza verificaciones defensivas idénticas a las del backend para impedir solicitudes fraudulentas o de programas sin HomeClass.

### 3. Vistas y AJAX (`views/portal_templates.xml`)

* Hereda de `irg_campus_certificates_portal.portal_certificate_new_override` para añadir el campo de sesión.
* Implementa lógica JS que escucha los eventos `change` en el selector de tipo de documento y el selector de libreta académica.
* Si el tipo es `attendance`, se invoca Fetch y se refrescan las opciones de sesiones al vuelo, mostrando u ocultando el bloque según corresponda.

---

## Suite de Pruebas Automatizadas

El módulo incluye un set de pruebas en `tests/test_attendance.py`:
- `test_01_attendance_requires_session`: Valida que sea imposible crear un registro tipo `attendance` sin asignarle una sesión.
- `test_02_attendance_restricted_to_homeclass_or_hc_batch`: Comprueba que no se permite crear una solicitud de asistencia en libretas normales de cursos presenciales u online que no contengan HomeClass.
- `test_03_attendance_allowed_on_hc_batch`: Verifica que se apruebe la solicitud en lotes con código "HC".
- `test_04_attendance_allowed_on_homeclass_modality`: Verifica que se apruebe la solicitud si el programa académico tiene asignada la modalidad HomeClass.
- `test_05_attendance_fill_template`: Comprueba la carga física de las plantillas Word y el flujo completo de generación de PDF.

---

## Instalación y Pruebas Locales

```bash
# Instalar y ejecutar tests
docker exec -it odoo16irg_local odoo -c /etc/odoo/odoo.conf -d test_irg_db -i irg_certificate_attendance --test-enable --stop-after-init
```
