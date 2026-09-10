# Survey como plantilla editable con snapshots privados

Cuando un flujo Portal necesita que usuarios internos editen preguntas con la
interfaz de Encuestas, pero no debe heredar las rutas públicas, tokens ni el
modelo de intentos de Survey, conviene separar plantilla y ejecución:

- Reutilizar `survey.survey`, `survey.question` y `survey.question.answer` solo
  para edición interna.
- Marcar explícitamente la encuesta como `template_only` y bloquear tanto
  `_create_answer` como `survey.user_input.create/write`. Configurar acceso por
  token no basta por sí solo: administradores o rutas futuras podrían crear un
  intento.
- Al iniciar el flujo, validar un contrato mínimo de secciones, tipos y opciones,
  y congelar título, ayuda, obligatoriedad, orden, opciones y claves técnicas en
  modelos privados del dominio.
- Guardar las respuestas únicamente en el snapshot privado. Así una edición o
  eliminación posterior de la plantilla no reinterpreta versiones históricas.
- Usar claves técnicas estables para la lógica y títulos congelados editables
  para la presentación.
- Las rutas Portal deben resolver primero la propiedad de negocio, bloquear la
  configuración y el borrador en un orden común, y validar que cada pregunta y
  opción pertenece al snapshot exacto.
- Los errores detallados del contrato de plantilla se registran en servidor y se
  transforman en un mensaje genérico antes de llegar al portal.

Este patrón evita que una herramienta cómoda de autoría se convierta en una
segunda superficie de autenticación, almacenamiento o exposición de respuestas.
