# Plan de Misión: Módulo de Burbuja de Chat n8n por Curso (`irg_n8n_chat_bubble`)

## 1. Alcance
El objetivo es crear un nuevo módulo en Odoo 16 (`irg_n8n_chat_bubble`) que agregue una burbuja de chat conectada a webhooks de n8n dentro del campus virtual (eLearning - `website_slides`).
Esta burbuja se configurará por curso (`op.course`), permitiendo asociar un webhook diferente (un agente especializado de n8n) por cada curso.
La burbuja de chat cargará dinámicamente el widget oficial de n8n (`@n8n/chat`) e inyectará en los metadatos de la conversación:
- Nombre del estudiante (`studentName`)
- Correo del estudiante (`studentEmail`)
- Nombre del curso académico (`courseName`)
- Nombre de la asignatura / canal del campus virtual (`subjectName`)

## 2. Clasificación de Complejidad
* **Tier:** `standard`
* **Justificación:** Se trata de un nuevo módulo que hereda de modelos del core (`op.course` de OpenEduCat y `slide.channel` de Odoo) e inyecta vistas QWeb y archivos Javascript en el frontend de Odoo. No afecta a la autenticación core ni a la concurrencia, ni elimina datos históricos, por lo que no requiere escalado a `complex`.

## 3. Modelos Elegidos por Rol
* **Orquestador (Plan):** Gemini 3.5 Flash
* **Codificador (Implementación):** Gemini 3.5 Flash (Tier Standard)
* **Testeador (Validación):** Gemini 3.5 Flash (Tier Standard)
* **Documentador (Documentación):** Gemini 3.5 Flash (Tier Standard)

## 4. Descomposición de Tareas
1. **Creación del esqueleto del módulo:** `irg_n8n_chat_bubble` en `addons-extra/extrairg/`.
2. **Modelos:**
   * Heredar de `op.course` en `models/op_course.py` para añadir campos de configuración de n8n (`irg_n8n_chat_enabled`, `irg_n8n_chat_webhook_url`, `irg_n8n_chat_title`, `irg_n8n_chat_welcome_msg`).
   * Heredar de `slide.channel` en `models/slide_channel.py` para añadir el método `irg_get_n8n_chat_config()` que obtiene la configuración del curso relacionado.
3. **Vistas:**
   * Crear la vista XML `views/op_course_views.xml` para añadir la pestaña de configuración del chat en el formulario del curso.
   * Crear la vista XML `views/website_slides_templates.xml` para heredar de `website_slides.layout` y `website_slides.slide_fullscreen` e inyectar el elemento DOM `#irg_n8n_chat_bubble_config`.
4. **Static Assets:**
   * Crear el script Javascript `static/src/js/n8n_chat_bubble.js` que detecta la configuración en el DOM, realiza la carga perezosa (lazy-loading) del CSS y JS de n8n, e inicializa el widget de chat con los metadatos del estudiante y del curso.
5. **Manifest y Accesos:**
   * Configurar `__manifest__.py` declarando las dependencias (`website_slides`, `openeducat_core`, `irg_course_convocatorias_v2`), las vistas y los assets en `web.assets_frontend`.
   * Incluir `__init__.py` para cargar los modelos.
6. **Validación:**
   * Validar localmente (en base a la estructura y sintaxis de Odoo 16).
   * Crear el archivo `verification.json` al completar la fase de testing.
