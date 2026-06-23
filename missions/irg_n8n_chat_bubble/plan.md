# Plan de Misión: Módulo de Burbuja de Chat n8n por Curso (`irg_n8n_chat_bubble`) - REINTENTO 2

## 1. Alcance
El objetivo es crear un nuevo módulo en Odoo 16 (`irg_n8n_chat_bubble`) que agregue una burbuja de chat conectada a webhooks de n8n dentro del campus virtual (eLearning - `website_slides`).
Esta burbuja se configurará por curso (`op.course`), permitiendo asociar un webhook diferente (un agente especializado de n8n) por cada curso.

## 2. Clasificación de Complejidad
* **Tier:** `complex`
* **Justificación:** Se detectó un error 500 en `/campus` porque en ciertas páginas la variable `channel` del contexto es un booleano (`False`), lo que provocó un `AttributeError` al intentar llamar a `irg_get_n8n_chat_config()`. Se aplica una validación ultra-segura basada en introspección (`hasattr`) para evitar errores en cualquier página del portal que use `website.layout`.

## 3. Modelos Elegidos por Rol
* **Orquestador (Plan):** Gemini 3.5 Flash
* **Codificador (Implementación):** Subagente Codificador (Gemini 3.5 Flash)
* **Testeador (Validación):** Subagente Testeador (Gemini 3.5 Flash)
* **Documentador (Documentación):** Subagente Documentador (Gemini 3.5 Flash)

## 4. Descomposición de Tareas
1. **Delegación a Subagente Codificador:**
   * Corregir `views/website_slides_templates.xml` para que el `t-if` verifique mediante introspección: `t-if="channel and hasattr(channel, 'irg_get_n8n_chat_config')"` en las dos plantillas heredadas.
2. **Delegación a Subagente Testeador:**
   * Validar sintaxis y emitir `verification.json` actualizado.
3. **Delegación a Subagente Documentador:**
   * Actualizar el log de ejecución, el walkthrough y la base de conocimiento con la resolución definitiva del bug de introspección de QWeb.
