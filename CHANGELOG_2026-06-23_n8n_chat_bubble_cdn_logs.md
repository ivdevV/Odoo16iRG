# Changelog - 2026-06-23 - CDN y Logs de Burbuja de Chat n8n

## Cambios realizados
1. **static/src/js/n8n_chat_bubble.js**:
   * Se removió el segmento de ruta `/code/` de las URLs de CDN de n8n.
   * Nueva URL de CSS: `https://cdn.jsdelivr.net/npm/@n8n/chat/dist/style.css`
   * Nueva URL de JS bundle: `https://cdn.jsdelivr.net/npm/@n8n/chat/dist/chat.bundle.es.js`

2. **models/slide_channel.py**:
   * Se importó el módulo estándar de python `logging`.
   * Se inicializó `_logger = logging.getLogger(__name__)`.
   * Se añadieron logs detallados en `irg_get_n8n_chat_config()` que registran:
     * Nombre, ID del canal y códigos/nombres de los cursos relacionados encontrados.
     * El estado de verificación de cada curso (código/nombre, si tiene habilitado el chat y su webhook).
     * El resultado final (si el chat queda habilitado o desactivado para el canal) y los datos retornados.

## Validación y Pruebas
* Sintaxis Python y JS comprobada exitosamente.
* Actualización de módulo (`-u irg_n8n_chat_bubble`) ejecutada exitosamente en el contenedor Docker local `odoo16irg_local`.
