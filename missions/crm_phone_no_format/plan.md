# Plan de Misión — crm_phone_no_format

## Alcance
Desactivar por completo el formateo de teléfonos y la adición de espacios en los campos de teléfono y móvil del modelo `crm.lead` en Odoo 16.

## Descomposición de la Tarea
1. Crear el nuevo módulo `irg_crm_phone_no_format` en `addons-extra/extrairg/`.
2. Definir `__manifest__.py` con dependencias en `crm` y `phone_validation`.
3. Crear el modelo `crm_lead.py` heredando de `crm.lead` para sobrescribir y anular `_phone_format` y los onchanges.
4. Crear la vista heredada de `crm.crm_lead_view_form` para forzar `widget="char"` en los campos de teléfono y móvil.
5. Instalar, probar y validar la persistencia del formato ingresado por el usuario.

## Clasificación de Complejidad
* **Tier:** `trivial` / `standard` (Creación de un módulo simple sin lógica compleja ni riesgo de datos).
* **Justificación:** El cambio consiste en deshabilitar validaciones y formateos en una sola pantalla/modelo sin tocar flujos de base de datos complejos.
* **Modelo Elegido:** Gemini 3.5 Flash (High).

## Modelos y Subagentes
* **Plan:** Agente Principal (Gemini 3.5 Flash)
* **Implementación:** Agente Principal (Gemini 3.5 Flash)
* **Validación:** Agente Principal (Gemini 3.5 Flash)
* **Documentación:** Agente Principal (Gemini 3.5 Flash)
