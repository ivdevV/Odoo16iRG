# Plan de Misión: Módulo de Burbuja de Chat n8n por Curso (`irg_n8n_chat_bubble`) - REINTENTO 3

## 1. Alcance
El objetivo es crear un nuevo módulo en Odoo 16 (`irg_n8n_chat_bubble`) que agregue una burbuja de chat conectada a webhooks de n8n dentro del campus virtual (eLearning - `website_slides`).
Esta burbuja se configurará por curso (`op.course`), permitiendo asociar un webhook diferente (un agente especializado de n8n) por cada curso.

## 2. Clasificación de Complejidad
* **Tier:** `complex`
* **Justificación:** Se detectó un error `TypeError: 'NoneType' object is not callable` al intentar evaluar `channel.irg_get_n8n_chat_config()` en `/campus`. Esto ocurre porque en ciertas páginas (o si el módulo no está completamente instalado/cargado en memoria), el ORM de Odoo o el proxy de QWeb interceptan la llamada y evalúan el atributo inexistente como `None` en lugar de lanzar `AttributeError`, engañando a `hasattr()`. Se implementa una validación defensiva absoluta usando `getattr(channel, 'irg_get_n8n_chat_config', None)` para asegurar que solo se intente llamar al método si este realmente existe y devuelve un objeto ejecutable.

## 3. Modelos Elegidos por Rol
* **Orquestador (Plan):** Gemini 3.5 Flash
* **Codificador (Implementación):** Subagente Codificador (Gemini 3.5 Flash)
* **Testeador (Validación):** Subagente Testeador (Gemini 3.5 Flash)
* **Documentador (Documentación):** Subagente Documentador (Gemini 3.5 Flash)

## 4. Descomposición de Tareas
1. **Delegación a Subagente Codificador:**
   * Modificar `views/website_slides_templates.xml` para reemplazar en ambas plantillas:
     `<t t-if="channel and hasattr(channel, 'irg_get_n8n_chat_config')">`
     Por:
     `<t t-if="channel and getattr(channel, 'irg_get_n8n_chat_config', None)">`
2. **Delegación a Subagente Testeador:**
   * Validar la sintaxis de los archivos.
   * Ejecutar la actualización del módulo en el contenedor de Odoo local para probar la consistencia y verificar si el error de renderizado 500 desaparece en local.
   * Actualizar `verification.json`.
3. **Delegación a Subagente Documentador:**
   * Actualizar log de ejecución, walkthrough y la base de conocimiento con este hallazgo sobre el comportamiento de introspección de proxies en Odoo 16 QWeb.
