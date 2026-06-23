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

* **Evitación de Errores de External ID, Variables Booleanas e Introspección Segura en Layouts (Odoo 16)**:
  Al inyectar scripts, estilos o componentes globales (como widgets flotantes) en vistas específicas de un submódulo (e.g. `website_slides`), heredar directamente de sus layouts específicos (como `website_slides.layout`) puede arrojar errores de External ID no encontrado debido al orden de carga de los módulos.
  La solución es heredar del layout base del portal web (`website.layout`) y aplicar una cláusula condicional con introspección segura: `<t t-if="channel and getattr(channel, 'irg_get_n8n_chat_config', None)">` para encapsular el pintado de los elementos. Esto previene un `AttributeError: 'bool' object has no attribute 'irg_get_n8n_chat_config'` cuando la variable `channel` está presente en el contexto pero se evalúa como un booleano (`False`), y el error `TypeError: 'NoneType' object is not callable` cuando Odoo evalúa un atributo inexistente como `None` (engañando a `hasattr`), garantizando que la burbuja de chat o el componente solo se renderice de forma segura si la variable es un recordset real con dicho método.
  Asimismo, es obligatorio declarar explícitamente `'website'` en la lista `'depends'` del `__manifest__.py` para garantizar que el ORM de Odoo resuelva las dependencias de QWeb layouts de `website` antes de compilar y registrar las plantillas extendidas.


## Estructura del Módulo
El módulo se encuentra en: `addons-extra/extrairg/irg_n8n_chat_bubble`
- `models/op_course.py`: Campos de configuración en `op.course`.
- `models/slide_channel.py`: Extracción de la configuración y de los datos del estudiante conectado.
- `views/op_course_views.xml`: Pestaña de configuración en formulario del curso en backend.
- `views/website_slides_templates.xml`: Hereda de `website.layout` (con condicional de presencia de `channel`) y `website_slides.slide_fullscreen` para pintar el contenedor de datos de configuración de forma segura.
- `static/src/js/n8n_chat_bubble.js`: Inicializador lazy-load del widget flotante de chat de n8n.
