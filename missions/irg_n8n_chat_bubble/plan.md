# Plan de Misión: Módulo de Burbuja de Chat n8n por Curso (`irg_n8n_chat_bubble`) - REINTENTO 1

## 1. Alcance
El objetivo es crear un nuevo módulo en Odoo 16 (`irg_n8n_chat_bubble`) que agregue una burbuja de chat conectada a webhooks de n8n dentro del campus virtual (eLearning - `website_slides`).
Esta burbuja se configurará por curso (`op.course`), permitiendo asociar un webhook diferente (un agente especializado de n8n) por cada curso.

## 2. Clasificación de Complejidad
* **Tier:** `complex` (Escalado reactivo desde `standard` tras fallo de instalación en el servidor)
* **Justificación:** El módulo falló al instalarse en Odoo debido a que el External ID `website_slides.layout` no existe en la base de datos de Odoo 16. Se escala para resolver el problema de herencia visual utilizando `website.layout` como fallback condicional robusto.

## 3. Modelos Elegidos por Rol
* **Orquestador (Plan):** Gemini 3.5 Flash
* **Codificador (Implementación):** Subagente Codificador (Gemini 3.5 Flash, heredando capacidad de razonamiento)
* **Testeador (Validación):** Subagente Testeador (Gemini 3.5 Flash)
* **Documentador (Documentación):** Subagente Documentador (Gemini 3.5 Flash)

## 4. Descomposición de Tareas
1. **Delegación a Subagente Codificador:**
   * Corregir `views/website_slides_templates.xml` para heredar de `website.layout` en lugar de `website_slides.layout`.
   * Verificar la consistencia de los archivos del módulo.
2. **Delegación a Subagente Testeador:**
   * Validar sintaxis y emitir `verification.json` actualizado.
3. **Delegación a Subagente Documentador:**
   * Actualizar el log de ejecución y la base de conocimiento para dejar constancia del error resuelto.
