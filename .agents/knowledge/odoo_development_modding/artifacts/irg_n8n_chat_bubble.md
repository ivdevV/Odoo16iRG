# Módulo Odoo 16: `irg_n8n_chat_bubble` (Configuración de Chat n8n)

## Aprendizaje y Convenciones de Diseño

* **Relación Curso - eLearning**:
  En la instancia actual, las asignaturas se gestionan como `slide.channel` (eLearning) y se asocian a cursos académicos `op.course` mediante el conector de convocatorias (`irg_course_convocatorias_v2`).
  Para asociar configuraciones a nivel de curso y repercutirlas en las asignaturas de dicho curso, se utiliza el método `_irg_get_related_courses()` heredado de `slide.channel` para resolver la relación.
  
* **Lazy Loading de Scripts Externos**:
  Para no penalizar el rendimiento del portal (SEO y Core Web Vitals) cargando librerías JavaScript pesadas en todas partes, se inyecta un tag `#irg_n8n_chat_bubble_config` oculto desde el servidor mediante QWeb. El Javascript del módulo frontend (`web.assets_frontend`) comprueba si el tag existe y, solo en ese caso, descarga de manera asíncrona mediante un `import()` dinámico el bundle ES y el CSS del widget de chat desde jsdelivr.
  
* **Paso de Metadatos Contextuales**:
  n8n permite enviar metadatos (`metadata`) en el widget de chat. Al inicializar el chat, se inyectan dinámicamente las variables correspondientes a:
  - `studentName` (Nombre del estudiante actual logueado)
  - `studentEmail` (Email del estudiante)
  - `courseName` (Nombre del curso académico)
  - `subjectName` (Nombre de la asignatura)
  Esto permite que el agente inteligente de n8n reciba en el webhook de chat toda la información del estudiante para responder de forma personalizada.

## Estructura del Módulo
El módulo se encuentra en: `addons-extra/extrairg/irg_n8n_chat_bubble`
- `models/op_course.py`: Campos de configuración en `op.course`.
- `models/slide_channel.py`: Extracción de la configuración y de los datos del estudiante conectado.
- `views/op_course_views.xml`: Pestaña de configuración en formulario del curso en backend.
- `views/website_slides_templates.xml`: Hereda de `website_slides.layout` y `website_slides.slide_fullscreen` para pintar el contenedor de datos.
- `static/src/js/n8n_chat_bubble.js`: Inicializador lazy-load del widget flotante de chat de n8n.
