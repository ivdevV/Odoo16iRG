# Plan - Misión `irg_n8n_chat_bubble_selector_fix`

Este plan detalla el alcance, la clasificación de complejidad y el diseño de la solución para corregir el selector CSS que impedía que el chat de n8n se visualizase en pantalla completa en el entorno de producción.

## Alcance
- Modificar el archivo [website_slides_templates.xml](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_n8n_chat_bubble/views/website_slides_templates.xml) para corregir el selector CSS del modo pantalla completa.
- Corregir el selector erróneo `body.n8n-chat-fullscreen :root` por `body.n8n-chat-fullscreen` y `body.n8n-chat-fullscreen .chat-window` para asegurar que el tamaño del chat cubra el 100% de la pantalla.

## Clasificación de Complejidad

| Tier | Justificación | Modelo Recomendado |
|------|---------------|-------------------|
| `trivial` | Afecta a 1 solo archivo, corrige un selector CSS sin lógica nueva, sin riesgos de seguridad o pérdida de datos. | Modelo ligero (gama `mini`/`nano`) |

*Nota: La fase de Planificación y Orquestación inicial fue realizada por el modelo de razonamiento de gama alta (parent).*

## Solución Propuesta

### Diagnóstico del Error
El selector CSS original era:
```css
body.n8n-chat-fullscreen :root { ... }
```
El selector `:root` es equivalente a `html`, que es el elemento padre de `body`. Por ende, el selector descendente `body.n8n-chat-fullscreen :root` busca un elemento `:root` dentro de `body`, lo cual nunca se cumple en la jerarquía HTML, impidiendo que se aplicasen los overrides de variables CSS y dimensiones.

### Modificaciones
Redefinir los selectores CSS en [website_slides_templates.xml](file:///Users/ivrogo/Workspace/Proyectos%20iRG/Odoo16iRG/addons-extra/extrairg/irg_n8n_chat_bubble/views/website_slides_templates.xml):
- `body.n8n-chat-fullscreen` para aplicar las variables CSS locales de la ventana.
- `body.n8n-chat-fullscreen .chat-window` para asegurar que el contenedor físico de la ventana del chat de n8n se expanda a `100vw` y `100vh` con un `max-height: 100vh`.

## Plan de Verificación

### Validación de Sintaxis
- Comprobación estática del XML del archivo modificado mediante ElementTree en Python.

### Validación de Integración en Odoo
- Ejecutar la actualización local en el contenedor Docker para asegurar que se integra en el registro de Qweb sin producir excepciones:
  ```bash
  docker exec -i odoo16irg_local odoo -c /etc/odoo/odoo.conf -u irg_n8n_chat_bubble -d odoo16irg_local --stop-after-init
  ```

### Verificación del Negocio (Manual)
- Comprobar que al pulsar el botón `⛶` en la interfaz del eLearning el chat pase a ocupar la pantalla completa en ordenadores.
