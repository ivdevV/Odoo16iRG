# Plan de Misión: Personalización y Estilización del Chat n8n (`irg_n8n_chat_bubble_customization`)

## 1. Alcance
El objetivo es personalizar la burbuja de chat de n8n en el módulo `irg_n8n_chat_bubble` de Odoo 16:
1. En `static/src/js/n8n_chat_bubble.js`:
   * Configurar `defaultLanguage: 'es'`.
   * Agregar la propiedad `i18n` con traducciones para 'es' y 'en'.
   * Remover los parámetros de nivel raíz (`title`, `subtitle` y `chatInputPlaceholder`).
2. En `views/website_slides_templates.xml`:
   * Inyectar una etiqueta `<style>` con variables CSS de diseño para `@n8n/chat` después del div `#irg_n8n_chat_bubble_config` cuando el chat esté habilitado en las plantillas `n8n_chat_bubble_course_main` y `n8n_chat_bubble_fullscreen`.

## 2. Clasificación de Complejidad
* **Tier:** `standard`
* **Justificación:** Afecta a 2 archivos, con lógica acotada en JS y XML de Odoo sin riesgos de seguridad ni modificaciones de base de datos o arquitectura.

## 3. Modelos Elegidos
* **Ejecutor (Subagente):** Antigravity (Gemini)

## 4. Descomposición de Tareas
1. **Implementación:**
   * Editar `static/src/js/n8n_chat_bubble.js` para reestructurar la inicialización del chat.
   * Editar `views/website_slides_templates.xml` para añadir el bloque de estilos CSS custom.
2. **Validación:**
   * Verificar la sintaxis JS y XML.
   * Ejecutar la actualización del módulo en el contenedor local de Docker-compose.
3. **Documentación:**
   * Registrar las actividades en `execution.log` y emitir `verification.json`.
   * Crear el archivo de diferencias `diff.patch`.
