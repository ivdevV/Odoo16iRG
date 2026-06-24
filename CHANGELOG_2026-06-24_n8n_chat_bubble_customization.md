# Changelog - 2026-06-24 - Personalización e Idioma de Burbuja de Chat n8n

## Cambios realizados
1. **static/src/js/n8n_chat_bubble.js**:
   * Se modificó la inicialización de `module.createChat` para soportar localización e internacionalización.
   * Se configuró `defaultLanguage: 'es'` para establecer el español como idioma predeterminado del widget.
   * Se introdujo la propiedad `i18n` con traducciones estructuradas para español (`es`) e inglés (`en`).
   * Se mapearon las propiedades de traducción:
     * `title`: El título del chat definido en el curso/canal (`title`).
     * `subtitle`: El mensaje de bienvenida configurado (`welcomeMsg`).
     * `getStarted`: "Iniciar chat" en `es` / "Start chat" en `en`.
     * `inputPlaceholder`: "Escribe tu consulta..." en `es` / "Type your question..." en `en`.
   * Se removieron los parámetros obsoletos a nivel raíz (`title`, `subtitle`, `chatInputPlaceholder`) ya que se gestionan bajo la propiedad `i18n`.

2. **views/website_slides_templates.xml**:
   * Se inyectó una etiqueta `<style>` con las variables CSS de estilización para `@n8n/chat`.
   * La inyección se colocó inmediatamente después del div `#irg_n8n_chat_bubble_config` cuando el chat esté habilitado (`t-if="n8n_config.get('enabled')"`).
   * La inyección de estilos se aplicó en las dos plantillas heredadas del módulo eLearning:
     * `n8n_chat_bubble_course_main` (que hereda de `website_slides.course_main`).
     * `n8n_chat_bubble_fullscreen` (que hereda de `website_slides.slide_fullscreen`).

## Validación y Pruebas
* **JavaScript**: Sintaxis verificada localmente de forma exitosa usando `vm.Script` en Node.js.
* **XML / QWeb**: Estructura del XML y etiquetas verificadas exitosamente en Python.
* **Odoo Registry**: Se actualizó el módulo `irg_n8n_chat_bubble` localmente en el contenedor `odoo16irg_local` de manera exitosa y sin reportar ningún error de carga de QWeb o Python registry.
