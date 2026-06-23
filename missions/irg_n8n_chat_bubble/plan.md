# Plan de Misión: Módulo de Burbuja de Chat n8n por Curso (`irg_n8n_chat_bubble`) - REINTENTO 6

## 1. Alcance
El objetivo es crear un nuevo módulo en Odoo 16 (`irg_n8n_chat_bubble`) que agregue una burbuja de chat conectada a webhooks de n8n dentro del campus virtual (eLearning - `website_slides`).
Esta burbuja se configurará por curso (`op.course`), permitiendo asociar un webhook diferente (un agente especializado de n8n) por cada curso.

## 2. Clasificación de Complejidad
* **Tier:** `complex`
* **Justificación:** El error 500 persiste debido a que Odoo no elimina de la base de datos (`ir.ui.view`) las plantillas que son removidas del archivo XML en el disco. La plantilla vieja `n8n_chat_bubble_layout` (que heredaba de `website.layout`) sigue existiendo huérfana y activa en la tabla `ir_ui_view` de la base de datos `Base16`. Para solucionarlo sin intervención manual, implementamos una plantilla de saneamiento en el XML con el mismo ID, pero vacía y sin `inherit_id`. Esto forzará a Odoo a sobrescribir el registro antiguo de la base de datos y a anular la herencia rota de forma automática al actualizar el módulo.

## 3. Modelos Elegidos por Rol
* **Orquestador (Plan):** Gemini 3.5 Flash
* **Codificador (Implementación):** Subagente Codificador (Gemini 3.5 Flash)
* **Testeador (Validación):** Subagente Testeador (Gemini 3.5 Flash)
* **Documentador (Documentación):** Subagente Documentador (Gemini 3.5 Flash)

## 4. Descomposición de Tareas
1. **Delegación a Subagente Codificador:**
   * Modificar `views/website_slides_templates.xml` para volver a declarar la plantilla con `id="n8n_chat_bubble_layout"`, pero sin `inherit_id` y con contenido vacío.
2. **Delegación a Subagente Testeador:**
   * Validar consistencia y sintaxis.
   * Ejecutar la actualización en local y actualizar `verification.json`.
3. **Delegación a Subagente Documentador:**
   * Actualizar log de ejecución, el walkthrough y la base de conocimiento documentando este gotcha crítico sobre el comportamiento del ORM de Odoo al remover vistas XML y cómo sanearlas.
