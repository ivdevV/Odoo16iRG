# Micro-Spec: IRG Practice Request Student Profile (2026-06-11)

## Objetivo

Ampliar el formulario portal de solicitud de prácticas con un perfil académico y profesional obligatorio para el alumno.

## Alcance

- Crear el módulo `irg_practice_request_student_profile` en `addons-extra/extrairg/`.
- Extender `practice.request` con campos `irg_*` para edad, formación académica, experiencia laboral, motivaciones, expectativas, objetivos y necesidades formativas.
- Heredar el formulario portal de `isep_practices_2` para insertar las preguntas después de `Curso` y antes de `Tipo de práctica`.
- Mostrar las preguntas de forma progresiva, evitando presentar todo el bloque de golpe.
- Heredar el controlador de `irg_practice_center_restrict` para conservar el flujo sin selección obligatoria de centro y guardar las respuestas nuevas.
- Validar en servidor que todas las preguntas del perfil estén respondidas antes de crear la solicitud.
- Mostrar los campos en backend dentro de la solicitud de prácticas.

## Fuera De Alcance

- No modificar `isep_practices_2` ni `irg_practice_center_restrict`.
- No cambiar el flujo de asignación manual de centros de práctica.
- No hacer obligatorios los campos a nivel modelo para no bloquear solicitudes históricas, cargas internas o integraciones.

## Criterios De Aceptación

- El portal muestra el bloque `Perfil del alumno` entre `Curso` y `Tipo de práctica`.
- El alumno navega el bloque por pasos con botones `Anterior` y `Siguiente`.
- No se puede enviar una solicitud portal si falta alguna pregunta del perfil.
- Un POST manual incompleto no crea la solicitud y devuelve error al formulario.
- Las respuestas se guardan en `practice.request`.
- El backend muestra las respuestas en una sección `Perfil del alumno`.

## Validación Esperada

- Tests unitarios de existencia de campos y persistencia de valores.
- Test de cobertura de los campos obligatorios definidos por el controlador portal.
- Actualización local del módulo en Odoo 16 mediante `docker-compose.local.yml` cuando el entorno esté disponible.

## Riesgos Y Mitigación

- Riesgo: los campos `required=True` a nivel modelo podrían romper flujos backend existentes.
- Mitigación: la obligatoriedad se limita al formulario portal y al controlador portal.
