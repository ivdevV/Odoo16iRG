# Micro-Spec: IRG Practice Preferred Quarter (2026-07-28)

## Objetivo

Añadir la pregunta obligatoria "Trimestre preferente para iniciar las prácticas" en el formulario portal de solicitud de prácticas, ubicada inmediatamente antes de "Tipo de práctica", almacenar la selección del alumno en la solicitud (`practice.request`) y visibilizarla en la vista backend.

## Alcance

- Crear el módulo `irg_practice_preferred_quarter` en `addons-extra/extrairg/`.
- Extender `practice.request` con el campo `irg_preferred_quarter` (Selection).
- Heredar la vista de formulario portal `isep_practices_2.practice_request_form_template` para insertar la pregunta antes de `Tipo de práctica` (`practice_center_type_id`).
- Las opciones del desplegable son:
  - `marzo_mayo`: "Marzo a Mayo"
  - `junio_agosto`: "Junio a Agosto"
  - `septiembre_noviembre`: "Septiembre a Noviembre"
  - `diciembre_febrero`: "Diciembre a Febrero"
- Heredar el controlador portal (`IrgPracticeRequestStudentProfile` / `IrgPracticeRequestRestrict` / `PracticeCenterPortal`) para validar y guardar la respuesta.
- Extender la vista de formulario backend (`isep_practices_2.view_practice_request_form`) para mostrar el campo.
- Incluir tests unitarios de validación del campo y guardado en portal.

## Fuera De Alcance

- No modificar directamente `isep_practices_2` ni otros módulos existentes.
- No alterar la lógica de perfiles ni de asignación de centros.

## Criterios De Aceptación

- El formulario portal muestra la pregunta "Trimestre preferente para iniciar las prácticas*" con la opción inicial "Escribe o selecciona una opción" justo antes de "Tipo de práctica".
- No se puede enviar la solicitud si no se ha seleccionado uno de los 4 trimestres.
- El valor seleccionado se guarda correctamente en el registro `practice.request` correspondiente.
- El backend muestra el trimestre preferente en la vista de formulario de la solicitud.
- La suite de tests unitarios del módulo pasa satisfactoriamente.
