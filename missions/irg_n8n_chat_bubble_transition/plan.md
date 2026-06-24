# Plan de Misión: Transición Fluida para Redimensionado de Chat (`irg_n8n_chat_bubble_transition`)

## 1. Alcance
El objetivo es agregar una regla CSS de transición fluida al inicio de los bloques `<style>` dentro de las plantillas heredadas `n8n_chat_bubble_course_main` y `n8n_chat_bubble_fullscreen` en `views/website_slides_templates.xml`.

La regla a añadir es:
```css
                        /* Transición fluida para el cambio de tamaño del chat */
                        .n8n-chat, 
                        .n8n-chat .chat-window {
                            transition: width 0.35s cubic-bezier(0.4, 0, 0.2, 1),
                                        height 0.35s cubic-bezier(0.4, 0, 0.2, 1),
                                        bottom 0.35s cubic-bezier(0.4, 0, 0.2, 1),
                                        right 0.35s cubic-bezier(0.4, 0, 0.2, 1),
                                        border-radius 0.35s cubic-bezier(0.4, 0, 0.2, 1) !important;
                        }
```

## 2. Clasificación de Complejidad
* **Tier:** `trivial`
* **Justificación:** Afecta a 1 solo archivo, sin lógica nueva ni riesgo de seguridad o datos, consistiendo puramente en una edición de estilos repetitiva.

## 3. Modelos Elegidos
* **Ejecutor (Subagente):** Antigravity (Gemini)

## 4. Descomposición de Tareas
1. **Implementación:**
   * Editar `views/website_slides_templates.xml` para insertar la regla CSS al inicio de ambos bloques `<style>`.
2. **Validación:**
   * Comprobar la validez sintáctica del archivo XML editado.
   * Ejecutar la actualización del módulo en el contenedor de desarrollo local Docker.
3. **Documentación:**
   * Registrar actividades en `execution.log` y emitir `verification.json` y `diff.patch`.
