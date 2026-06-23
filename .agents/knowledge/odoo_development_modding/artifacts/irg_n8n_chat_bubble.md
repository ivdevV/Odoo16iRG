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
  - This allows the n8n intelligent agent to receive all context parameters in the webhook to personalize responses.

* **Evitación de Errores de Contexto y QWeb SafeEval (Odoo 16)**:
  Heredar del layout global del portal web (`website.layout`) para inyectar elementos condicionales basados en variables del contexto de una página particular (como `channel` de eLearning) puede ser problemático. Si el usuario navega a páginas globales (como `/campus`), la variable `channel` puede no existir, o evaluarse como un booleano `False` o un objeto no válido, disparando errores de tipo `AttributeError` o `TypeError` en el motor de renderizado de Odoo.
  Para evitarlo de raíz:
  1. Se debe acotar la herencia a las vistas específicas de eLearning donde dicha variable existe de forma natural: `website_slides.course_main` y `website_slides.slide_fullscreen`.
  2. En estas vistas, `channel` siempre es el recordset esperado de `slide.channel`, permitiendo aplicar un condicional directo `<t t-if="channel">` sin necesidad de métodos complejos de introspección como `getattr` o `hasattr`.
  3. Declarar explícitamente `'website'` y `'website_slides'` en la sección `'depends'` del manifiesto del módulo (`__manifest__.py`) para asegurar que el orden de carga del ORM resuelva e instale los módulos requeridos antes de registrar las nuevas plantillas extendidas.

* **Saneamiento de Vistas Huérfanas en BD (active="False")**:
  En Odoo, si una plantilla XML de herencia (como `inherit_id="website.layout"`) es eliminada del código fuente, Odoo **no la elimina automáticamente de la base de datos** (`ir.ui.view`) durante la actualización del módulo. El registro huérfano permanece activo en la base de datos, lo que puede causar errores 500 persistentes si intenta evaluar variables del contexto inexistentes o llamadas inválidas en el frontend.
  Para sanear estas vistas de forma totalmente automatizada y nativa sin recurrir a consultas SQL manuales ni intervención en el cliente:
  1. Mantén la declaración de la plantilla en el archivo XML con el mismo `id` e `inherit_id`.
  2. Añade el atributo `active="False"` a la definición de la plantilla para indicarle a Odoo que la desactive en base de datos.
  3. Proporciona un `xpath` inofensivo y válido sobre la plantilla padre (por ejemplo, inyectando un comentario vacío en un contenedor genérico como `<xpath expr="//div[@id='wrapwrap']" position="inside">`).
  Al actualizar el módulo, Odoo sobreescribirá el registro antiguo con esta nueva versión, desactivando efectivamente la herencia rota de manera nativa y segura.


## Estructura del Módulo
El módulo se encuentra en: `addons-extra/extrairg/irg_n8n_chat_bubble`
- `models/op_course.py`: Campos de configuración en `op.course`.
- `models/slide_channel.py`: Extracción de la configuración y de los datos del estudiante conectado.
- `views/op_course_views.xml`: Pestaña de configuración en formulario del curso en backend.
- `views/website_slides_templates.xml`: Herencias en `website_slides.course_main` y `website_slides.slide_fullscreen` para inyectar el contenedor de inicialización de la burbuja de chat de n8n de manera acotada y segura.
- `static/src/js/n8n_chat_bubble.js`: Inicializador lazy-load del widget flotante de chat de n8n.

## CDN y Diagnóstico de n8n Chat (Actualización 2026-06-23)
* **CDN de n8n**:
  Las URLs de CDN para el widget `@n8n/chat` deben apuntar directamente a `dist/` omitiendo el segmento intermedio `/code/`.
  - CSS: `https://cdn.jsdelivr.net/npm/@n8n/chat/dist/style.css`
  - JS: `https://cdn.jsdelivr.net/npm/@n8n/chat/dist/chat.bundle.es.js`

* **Debugging y Logging**:
  Para diagnosticar problemas en la carga de la burbuja en el frontend, `irg_get_n8n_chat_config()` usa el logger de Odoo para reportar el proceso de búsqueda:
  - Nombre e ID del canal y los códigos de todos los cursos OpenEduCat relacionados.
  - Estado de validación para cada curso (si el chat está habilitado y si cuenta con URL de webhook).
  - Configuración final devuelta.

