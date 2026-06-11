# irg_practice_request_student_profile

## Objetivo

Extiende las solicitudes de prácticas (`practice.request`) con un perfil académico y profesional del alumno, visible tanto en backend como en el formulario portal de creación de solicitudes.

## Alcance

- Añade campos `irg_*` al modelo `practice.request` para edad, formación, experiencia, empleo actual, motivación, expectativas y objetivos.
- Inserta una página de backend `Perfil del alumno` en la vista `isep_practices_2.view_practice_request_form`.
- Hereda la plantilla portal `isep_practices_2.practice_request_form_template` e inserta una interfaz progresiva de 3 pasos después del campo `course_id`.
- Oculta el resto del formulario hasta que el alumno complete correctamente el bloque `Perfil del alumno`.
- Hereda el controlador `IrgPracticeRequestRestrict` y conserva su comportamiento de creación sin centro obligatorio para alumnos portal, añadiendo los nuevos valores al `create`.
- Obliga a responder todas las preguntas del perfil en el portal mediante validación HTML y validación servidor antes de crear la solicitud.

## Uso

Instalar el módulo `irg_practice_request_student_profile`. Los alumnos deben completar el bloque `Perfil del alumno` en el portal antes de seleccionar el tipo de práctica. Los campos se guardan en la solicitud y quedan disponibles en backend.

## Validación

- Tests añadidos en `tests/test_practice_request_student_profile.py` para comprobar existencia de campos y persistencia en creación.

## Limitaciones

- La obligatoriedad se aplica al flujo portal de nueva solicitud. Los campos no se marcan como `required=True` a nivel modelo para no bloquear creaciones internas, importaciones o solicitudes históricas.
- La interfaz progresiva usa CSS/JS inline en QWeb para evitar build step y mantener compatibilidad con Odoo 16/Bootstrap.

## Changelog

- `16.0.1.0.0`: módulo inicial con campos de perfil, vistas backend/portal, controlador portal, obligatoriedad en portal, ocultación progresiva del resto del formulario y tests.
