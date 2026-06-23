# Plan de Misión: Módulo de Burbuja de Chat n8n por Curso (`irg_n8n_chat_bubble`) - REINTENTO 4

## 1. Alcance
El objetivo es crear un nuevo módulo en Odoo 16 (`irg_n8n_chat_bubble`) que agregue una burbuja de chat conectada a webhooks de n8n dentro del campus virtual (eLearning - `website_slides`).
Esta burbuja se configurará por curso (`op.course`), permitiendo asociar un webhook diferente (un agente especializado de n8n) por cada curso.

## 2. Clasificación de Complejidad
* **Tier:** `complex`
* **Justificación:** El error 500 persiste en el servidor del usuario debido a que el comando de actualización `-u` no realiza ninguna acción si el módulo nunca llegó a marcarse como instalado con éxito tras el fallo inicial (estado "No instalado"). Adicionalmente, agregamos explícitamente `website` en las dependencias del manifest para asegurar la resolución de layouts de QWeb en el orden de carga correcto del ORM.

## 3. Modelos Elegidos por Rol
* **Orquestador (Plan):** Gemini 3.5 Flash
* **Codificador (Implementación):** Subagente Codificador (Gemini 3.5 Flash)
* **Testeador (Validación):** Subagente Testeador (Gemini 3.5 Flash)
* **Documentador (Documentación):** Subagente Documentador (Gemini 3.5 Flash)

## 4. Descomposición de Tareas
1. **Delegación a Subagente Codificador:**
   * Modificar `__manifest__.py` para agregar `'website'` a la lista de dependencias (`'depends'`).
2. **Delegación a Subagente Testeador:**
   * Validar consistencia y sintaxis de los archivos.
   * Ejecutar la actualización en local y actualizar `verification.json`.
3. **Delegación a Subagente Documentador:**
   * Actualizar el log de ejecución, el walkthrough y la base de conocimiento indicando la necesidad imperativa de usar el comando de instalación `-i` en lugar de actualización `-u` si la base de datos del servidor se encuentra en un estado huérfano e inconsistente.
