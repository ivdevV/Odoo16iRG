# Plan de Misión: Módulo de Burbuja de Chat n8n por Curso (`irg_n8n_chat_bubble`) - REINTENTO 5

## 1. Alcance
El objetivo es crear un nuevo módulo en Odoo 16 (`irg_n8n_chat_bubble`) que agregue una burbuja de chat conectada a webhooks de n8n dentro del campus virtual (eLearning - `website_slides`).
Esta burbuja se configurará por curso (`op.course`), permitiendo asociar un webhook diferente (un agente especializado de n8n) por cada curso.

## 2. Clasificación de Complejidad
* **Tier:** `complex`
* **Justificación:** El error `TypeError: 'NoneType' object is not callable` se debe a que la herencia sobre `website.layout` se ejecuta de forma global en todo el portal web, donde la variable `channel` es a veces un booleano `False` o un objeto que en el entorno restringido de QWeb (SafeEval) se evalúa de manera inconsistente. Se corrige rediseñando la arquitectura de herencia: eliminamos la inyección en `website.layout` y la acotamos estrictamente a las plantillas específicas de eLearning (`website_slides.course_main` y `website_slides.slide_fullscreen`). En estas vistas de la asignatura, `channel` es de forma nativa e incondicional un recordset válido de `slide.channel`, evitando de raíz cualquier excepción en `/campus` u otras rutas.

## 3. Modelos Elegidos por Rol
* **Orquestador (Plan):** Gemini 3.5 Flash
* **Codificador (Implementación):** Subagente Codificador (Gemini 3.5 Flash)
* **Testeador (Validación):** Subagente Testeador (Gemini 3.5 Flash)
* **Documentador (Documentación):** Subagente Documentador (Gemini 3.5 Flash)

## 4. Descomposición de Tareas
1. **Delegación a Subagente Codificador:**
   * Modificar `views/website_slides_templates.xml` para eliminar la plantilla `n8n_chat_bubble_layout` que hereda de `website.layout`.
   * Crear en su lugar la plantilla `n8n_chat_bubble_course_main` que hereda de `website_slides.course_main` y se inyecta al final de la clase `o_wslides_course_main`.
   * Mantener la plantilla `n8n_chat_bubble_fullscreen` que hereda de `website_slides.slide_fullscreen`.
   * En ambas plantillas, remover el condicional `getattr` o `hasattr` redundante y simplificar a `<t t-if="channel">` o comprobar de forma estándar, ya que en el contexto específico de estas vistas de asignatura, `channel` siempre es el recordset esperado.
2. **Delegación a Subagente Testeador:**
   * Validar sintaxis, compilar el módulo localmente en Docker y comprobar logs.
   * Actualizar `verification.json`.
3. **Delegación a Subagente Documentador:**
   * Actualizar log de ejecución, el walkthrough y la base de conocimiento con la arquitectura de herencia segura definitiva y acotada a nivel de vista de eLearning.
