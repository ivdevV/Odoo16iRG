# Changelog - 2026-06-24 - Corrección del Selector CSS del Chat de n8n

## Descripción de los Cambios

### style(eLearning): fix fullscreen CSS selector for n8n chat bubble
Se ha corregido el selector CSS de pantalla completa del asistente de chat de n8n para que sea operativo en el entorno de producción.

* **Archivo modificado**: `addons-extra/extrairg/irg_n8n_chat_bubble/views/website_slides_templates.xml`
* **Cambio**:
  - Se corrigió el selector inválido `body.n8n-chat-fullscreen :root` por `body.n8n-chat-fullscreen` y `body.n8n-chat-fullscreen .chat-window`.
  - Se añadieron estilos explícitos de ancho y alto de pantalla (`100vw`, `100vh`, `max-height: 100vh`) a la clase `.chat-window` para asegurar que el contenedor de chat cubra la pantalla completa en modo expandido.

## Motivo
El selector `:root` apunta al elemento raíz `html`. Buscar `:root` de manera descendente dentro de `body` (como en `body.n8n-chat-fullscreen :root`) resulta en un selector inválido e inoperante en HTML, lo cual impedía al navegador aplicar los overrides de posicionamiento al presionar el botón `⛶` en producción.

## Validación y Verificación
* **Análisis Sintáctico**: Verificación estática XML exitosa con ElementTree en Python.
* **Prueba en Docker**: La actualización en caliente del módulo se realizó correctamente en la base de datos local `odoo16irg_local` en el contenedor Docker (`odoo -u irg_n8n_chat_bubble`) sin lanzar excepciones de compilación de plantillas QWeb.
